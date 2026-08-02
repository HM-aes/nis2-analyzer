"""
NIS2 Dashboard Views
All views use LoginRequiredMixin and talk to the existing compliance_engine API/models.
HTMX partial views return HTML fragments only.
"""

import json
import threading
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

from compliance_engine.models import (
    Client,
    ComplianceAudit,
    ComplianceGap,
    ClientDocument,
)


# ─── Valid Status Transitions ─────────────────────────────────────────────────

VALID_TRANSITIONS = {
    'REVIEW': ['COMPLETE', 'INTAKE'],
    'COMPLETE': ['DELIVERED', 'INTAKE'],
    'DELIVERED': [],
    'INTAKE': ['PROCESSING'],
    'PROCESSING': ['INTAKE'],
    'ANALYSIS': ['INTAKE'],
    'ERROR': ['INTAKE'],
}


# ─── Document Upload ──────────────────────────────────────────────────────────


class UploadDocumentView(LoginRequiredMixin, View):
    """Accept a file upload, store it, and kick off text extraction."""
    login_url = "/login/"

    def post(self, request, pk):
        audit = get_object_or_404(ComplianceAudit, pk=pk)
        uploaded_file = request.FILES.get("file")
        document_type = request.POST.get("document_type", "OTHER")

        if not uploaded_file:
            return HttpResponse("Geen bestand geselecteerd.", status=400)

        # Validate extension
        name = uploaded_file.name.lower()
        if not any(name.endswith(ext) for ext in [".pdf", ".docx", ".txt"]):
            return HttpResponse("Alleen PDF, DOCX of TXT bestanden.", status=400)

        doc = ClientDocument.objects.create(
            audit=audit,
            document_type=document_type,
            file=uploaded_file,
            original_filename=uploaded_file.name,
            file_size_bytes=uploaded_file.size,
            uploaded_by=request.user,
        )

        # Extract text in background thread (non-blocking)
        def _extract(doc_id):
            try:
                from docling.document_converter import DocumentConverter
                d = ClientDocument.objects.get(pk=doc_id)
                converter = DocumentConverter()
                result = converter.convert(d.file.path)
                d.text_extracted = True
                d.processed = True
                d.save(update_fields=["text_extracted", "processed"])
                logger.info(f"Text extracted from {d.original_filename}")
            except Exception as e:
                logger.error(f"Extraction error for {doc_id}: {e}")
                ClientDocument.objects.filter(pk=doc_id).update(
                    processing_error=str(e)
                )

        threading.Thread(target=_extract, args=(doc.pk,), daemon=True).start()

        # Update audit document count
        audit.documents_uploaded = audit.documents.count()
        audit.save(update_fields=["documents_uploaded"])

        messages.success(request, f'Document "{doc.original_filename}" geüpload')
        # Redirect back to documents tab
        return redirect(f"/dashboard/audits/{audit.pk}/?tab=documents")


# ─── Run AI Audit ─────────────────────────────────────────────────────────────


class RunAuditView(LoginRequiredMixin, View):
    """Trigger RAG + Gemini gap analysis pipeline for an audit."""
    login_url = "/login/"

    def post(self, request, pk):
        audit = get_object_or_404(ComplianceAudit, pk=pk)

        if audit.status != "INTAKE":
            return HttpResponse(
                "Audit is niet in de INTAKE-fase.", status=400
            )

        if not audit.documents.exists():
            return HttpResponse(
                "Upload eerst minimaal één document.", status=400
            )

        # Transition to PROCESSING
        audit.status = "PROCESSING"
        audit.started_at = timezone.now()
        audit.save(update_fields=["status", "started_at"])

        # Run pipeline in background so request returns immediately
        def _run_pipeline(audit_id):
            _run_nis2_pipeline(audit_id)

        threading.Thread(target=_run_pipeline, args=(audit.pk,), daemon=True).start()

        # Redirect to audit detail — HTMX polling will track status
        return redirect(f"/dashboard/audits/{audit.pk}/")


def _run_nis2_pipeline(audit_id):
    """Background worker: RAG search → Gemini analysis → save gaps."""
    import django
    try:
        from compliance_engine.models import ComplianceAudit, ComplianceGap, ClientDocument
        from nis2_agents.auditor import NIS2Auditor
        from rag_engine.qdrant_client import NIS2QdrantClient
        from django.utils import timezone

        audit = ComplianceAudit.objects.get(pk=audit_id)

        # ── Step 1: Collect text from uploaded documents ──────────────────────
        docs_text = []
        for doc in audit.documents.all():
            try:
                from docling.document_converter import DocumentConverter
                converter = DocumentConverter()
                result = converter.convert(doc.file.path)
                text = result.document.export_to_markdown()
                docs_text.append(text[:6000])  # cap per doc
                logger.info(f"Extracted text from {doc.original_filename}")
            except Exception as e:
                logger.warning(f"Could not extract {doc.original_filename}: {e}")
                # Fall back to filename as minimal context
                docs_text.append(f"Document: {doc.original_filename} ({doc.get_document_type_display()})")

        combined_text = "\n\n---\n\n".join(docs_text)

        if not combined_text.strip():
            audit.status = "INTAKE"
            audit.save(update_fields=["status"])
            logger.error(f"No text extracted for audit {audit_id}")
            return

        audit.status = "ANALYSIS"
        audit.save(update_fields=["status"])

        # ── Step 2: RAG — retrieve relevant NIS2 requirements ─────────────────
        qdrant = NIS2QdrantClient()
        nis2_chunks = []
        for query in [
            "NIS2 cybersecurity risk management measures",
            "incident response reporting obligations essential entities",
            "supply chain security requirements NIS2",
            "access control authentication NIS2 directive",
            "logging monitoring NIS2 compliance",
        ]:
            results = qdrant.search(query, top_k=5)
            nis2_chunks.extend([r["text"] for r in results])

        # Deduplicate chunks
        seen = set()
        unique_chunks = []
        for chunk in nis2_chunks:
            key = chunk[:100]
            if key not in seen:
                seen.add(key)
                unique_chunks.append(chunk)

        # ── Step 3: Gemini gap analysis ───────────────────────────────────────
        auditor = NIS2Auditor()
        import asyncio
        gap_analysis = asyncio.run(
            auditor.analyze_compliance(combined_text, unique_chunks[:25])
        )

        # ── Step 4: Save gaps to database ─────────────────────────────────────
        for gap_data in gap_analysis.gaps:
            ComplianceGap.objects.create(
                audit=audit,
                category=_normalise_category(gap_data.category),
                severity=gap_data.severity,
                title=gap_data.title,
                description=gap_data.recommendation,
                nis2_article=gap_data.nis2_article,
                nis2_requirement=gap_data.required_state,
                current_state=gap_data.current_state,
                required_state=gap_data.required_state,
                recommendation=gap_data.recommendation,
                estimated_effort_hours=gap_data.estimated_effort_hours,
                risk_score=gap_data.risk_score,
            )

        # ── Step 5: Finalise audit record ──────────────────────────────────────
        audit.gaps_identified = len(gap_analysis.gaps)
        audit.compliance_score = gap_analysis.overall_compliance_score
        audit.status = "REVIEW"
        audit.completed_at = timezone.now()
        # TASK 17: Set report_generated=True so download button appears
        audit.report_generated = True
        audit.report_generated_at = timezone.now()
        audit.save(update_fields=[
            "gaps_identified", "compliance_score", "status", "completed_at",
            "report_generated", "report_generated_at",
        ])
        logger.info(
            f"Audit {audit_id} complete: {len(gap_analysis.gaps)} gaps, "
            f"score {gap_analysis.overall_compliance_score:.1f}%"
        )

    except Exception as e:
        logger.error(f"Pipeline error for audit {audit_id}: {e}", exc_info=True)
        try:
            ComplianceAudit.objects.filter(pk=audit_id).update(
                status="INTAKE",
                internal_notes=f"Pipeline fout: {e}",
            )
        except Exception:
            pass


def _normalise_category(cat: str) -> str:
    """Map Gemini category strings to model CATEGORY_CHOICES keys."""
    mapping = {
        "TECHNICAL": "TECHNICAL",
        "ORGANIZATIONAL": "ORGANIZATIONAL",
        "INCIDENT_RESPONSE": "INCIDENT_RESPONSE",
        "SUPPLY_CHAIN": "SUPPLY_CHAIN",
        "ACCESS_CONTROL": "ACCESS_CONTROL",
        "LOGGING": "LOGGING",
        "TRAINING": "TRAINING",
        "GOVERNANCE": "GOVERNANCE",
        "ENCRYPTION": "ENCRYPTION",
    }
    return mapping.get(cat.upper(), "OTHER")


# ─── Timeline Builder ─────────────────────────────────────────────────────────


def build_audit_timeline(audit, gaps, documents):
    """Assemble chronological timeline events from existing model timestamps."""
    events = []

    events.append({
        'timestamp': audit.created_at,
        'type': 'created',
        'icon': '📋',
        'title': 'Audit aangemaakt',
        'detail': f'Tier {audit.tier} — €{audit.quoted_price}',
    })

    for doc in documents:
        events.append({
            'timestamp': doc.uploaded_at,
            'type': 'document',
            'icon': '📄',
            'title': 'Document geüpload',
            'detail': doc.original_filename,
        })

    if audit.started_at:
        events.append({
            'timestamp': audit.started_at,
            'type': 'processing',
            'icon': '🤖',
            'title': 'AI analyse gestart',
            'detail': 'Claude NIS2 analyse actief',
        })

    for gap in gaps.order_by('created_at'):
        events.append({
            'timestamp': gap.created_at,
            'type': 'gap',
            'icon': '🔴' if gap.severity == 'CRITICAL'
                    else '⚠️' if gap.severity == 'HIGH'
                    else '🟡',
            'title': f'Gap gevonden: {gap.title}',
            'detail': f'{gap.severity} — {gap.category}',
        })

    if audit.completed_at:
        events.append({
            'timestamp': audit.completed_at,
            'type': 'completed',
            'icon': '✅',
            'title': 'Analyse voltooid',
            'detail': f'Score: {audit.compliance_score}%',
        })

    if audit.delivered_at:
        events.append({
            'timestamp': audit.delivered_at,
            'type': 'delivered',
            'icon': '🚀',
            'title': 'Rapport geleverd aan klant',
            'detail': '',
        })

    return sorted(events, key=lambda x: x['timestamp'], reverse=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────


def is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def _initials(name):
    """First letters of up to two words — used for the activity-feed avatar."""
    parts = [p for p in (name or "").split() if p]
    if not parts:
        return "?"
    return "".join(p[0] for p in parts[:2]).upper()


# ─── Auth ─────────────────────────────────────────────────────────────────────


class DashboardLoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard:home")
        return render(request, "dashboard/login.html")

    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(request.GET.get("next", "dashboard:home"))
        return render(
            request, "dashboard/login.html", {"error": "Ongeldige inloggegevens."}
        )


class DashboardLogoutView(LoginRequiredMixin, View):
    login_url = "/login/"

    def post(self, request):
        logout(request)
        return redirect("home")


# ─── Dashboard Home ────────────────────────────────────────────────────────────


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        clients_qs = (
            Client.objects.all()
            if user.is_superuser
            else Client.objects.filter(account_manager=user)
        )
        audits_qs = ComplianceAudit.objects.filter(client__in=clients_qs)
        gaps_qs = ComplianceGap.objects.filter(audit__in=audits_qs)

        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # KPI
        ctx["total_clients"] = clients_qs.count()
        ctx["new_clients_month"] = clients_qs.filter(
            created_at__gte=month_start
        ).count()
        ctx["active_audits"] = audits_qs.exclude(
            status__in=["COMPLETE", "DELIVERED"]
        ).count()
        ctx["processing_audits"] = audits_qs.filter(status="PROCESSING").count()

        completed = audits_qs.filter(status__in=["COMPLETE", "DELIVERED"]).exclude(
            compliance_score__isnull=True
        )
        ctx["avg_score"] = round(
            float(completed.aggregate(avg=Avg("compliance_score"))["avg"] or 0), 1
        )
        ctx["completed_count"] = completed.count()
        ctx["critical_gaps"] = gaps_qs.filter(
            severity="CRITICAL", addressed=False
        ).count()

        # Revenue (admin only)
        if user.is_superuser:
            ctx["revenue_quoted"] = (
                audits_qs.filter(created_at__gte=month_start).aggregate(
                    s=Sum("quoted_price")
                )["s"]
                or 0
            )
            ctx["revenue_paid"] = (
                audits_qs.filter(paid=True, created_at__gte=month_start).aggregate(
                    s=Sum("actual_price")
                )["s"]
                or 0
            )
            ctx["revenue_unpaid"] = (
                audits_qs.filter(paid=False).aggregate(s=Sum("quoted_price"))["s"] or 0
            )

        # Kanban pipeline
        statuses = [
            "INTAKE",
            "PROCESSING",
            "ANALYSIS",
            "REVIEW",
            "COMPLETE",
            "DELIVERED",
        ]
        pipeline = []
        for s in statuses:
            col_audits = (
                audits_qs.filter(status=s)
                .select_related("client")
                .order_by("-created_at")
            )
            pipeline.append(
                {
                    "status": s,
                    "count": col_audits.count(),
                    "audits": col_audits[:3],
                    "extra": max(0, col_audits.count() - 3),
                }
            )
        ctx["pipeline"] = pipeline

        # Score distribution buckets
        buckets = [0, 0, 0, 0, 0]
        for audit in completed:
            score = float(audit.compliance_score or 0)
            idx = min(int(score // 20), 4)
            buckets[idx] += 1
        ctx["score_buckets"] = buckets
        ctx["score_bucket_max"] = max(buckets) if any(buckets) else 1

        # Gaps by category
        cat_data = (
            gaps_qs.values("category", "severity")
            .annotate(n=Count("id"))
            .order_by("category")
        )
        cats = {}
        for row in cat_data:
            c = row["category"]
            if c not in cats:
                cats[c] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
            cats[c][row["severity"]] = row["n"]
        ctx["gap_categories"] = [
            {
                "name": k,
                "label": k.replace("_", " ").title(),
                **v,
                "total": v["CRITICAL"] + v["HIGH"] + v["MEDIUM"] + v["LOW"],
            }
            for k, v in cats.items()
        ]
        ctx["gap_cat_max"] = max((c["total"] for c in ctx["gap_categories"]), default=1)

        # Recent activity — last 20 completed/changed audits
        ctx["recent_audits"] = audits_qs.select_related("client").order_by(
            "-updated_at"
        )[:10]
        ctx["recent_gaps"] = (
            gaps_qs.filter(severity__in=["CRITICAL", "HIGH"])
            .select_related("audit__client")
            .order_by("-created_at")[:10]
        )

        # Unified activity feed (audits + gaps, newest first) for the
        # dashboard-home activity panel — one real, timestamp-sorted stream
        # instead of two disjoint lists.
        activity = []
        for audit in ctx["recent_audits"]:
            activity.append({
                "timestamp": audit.updated_at,
                "client_name": audit.client.company_name,
                "initials": _initials(audit.client.company_name),
                "headline": audit.get_status_display(),
                "url": reverse("dashboard:audit_detail", args=[audit.pk]),
                "badge_class": f"badge-{audit.status.lower()}",
                "badge_label": audit.get_status_display(),
            })
        for gap in ctx["recent_gaps"]:
            activity.append({
                "timestamp": gap.created_at,
                "client_name": gap.audit.client.company_name,
                "initials": _initials(gap.audit.client.company_name),
                "headline": gap.title,
                "url": reverse("dashboard:audit_detail", args=[gap.audit.pk]),
                "badge_class": f"badge-{gap.severity.lower()}",
                "badge_label": gap.get_severity_display(),
            })
        activity.sort(key=lambda a: a["timestamp"], reverse=True)
        ctx["recent_activity"] = activity[:8]

        return ctx


# ─── Clients ───────────────────────────────────────────────────────────────────


class ClientsView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/clients.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        qs = (
            Client.objects.all()
            if user.is_superuser
            else Client.objects.filter(account_manager=user)
        )
        ctx["clients"] = qs.prefetch_related("audits").order_by("company_name")
        ctx["sectors"] = Client.SECTOR_CHOICES
        ctx["sizes"] = Client.COMPANY_SIZE_CHOICES
        ctx["total_clients"] = qs.count()
        return ctx


class ClientDetailView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/client_detail.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        client = get_object_or_404(Client, pk=kwargs["pk"])
        ctx["client"] = client
        ctx["sectors"] = Client.SECTOR_CHOICES
        ctx["sizes"] = Client.COMPANY_SIZE_CHOICES
        ctx["country_choices"] = Client.COUNTRY_CHOICES
        audits = client.audits.order_by("-created_at")
        ctx["audits"] = audits
        completed = audits.filter(status__in=["COMPLETE", "DELIVERED"]).exclude(
            compliance_score__isnull=True
        )
        ctx["completed_audits"] = completed
        ctx["trend_scores"] = list(
            completed.order_by("completed_at").values_list(
                "compliance_score", flat=True
            )
        )
        # Sector benchmark
        peers = ComplianceAudit.objects.filter(
            client__sector=client.sector, status__in=["COMPLETE", "DELIVERED"]
        ).exclude(compliance_score__isnull=True)
        ctx["sector_avg"] = round(
            float(peers.aggregate(avg=Avg("compliance_score"))["avg"] or 0), 1
        )
        ctx["latest_audit"] = audits.first()
        return ctx


class NewClientView(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request):
        return render(
            request,
            "dashboard/client_new.html",
            {
                "sectors": Client.SECTOR_CHOICES,
                "sizes": Client.COMPANY_SIZE_CHOICES,
                "country_choices": Client.COUNTRY_CHOICES,
            },
        )

    def post(self, request):
        data = request.POST
        errors = {}

        kvk = data.get("kvk_number", "").strip()
        if len(kvk) != 8 or not kvk.isdigit():
            errors["kvk_number"] = "KVK-nummer moet precies 8 cijfers zijn."
        elif Client.objects.filter(kvk_number=kvk).exists():
            errors["kvk_number"] = "Dit KVK-nummer bestaat al."

        required = [
            "company_name",
            "sector",
            "company_size",
            "contact_person",
            "email",
            "address",
            "city",
            "postal_code",
        ]
        for field in required:
            if not data.get(field, "").strip():
                errors[field] = "Dit veld is verplicht."

        if errors:
            return render(
                request,
                "dashboard/client_new.html",
                {
                    "errors": errors,
                    "data": data,
                    "sectors": Client.SECTOR_CHOICES,
                    "sizes": Client.COMPANY_SIZE_CHOICES,
                    "country_choices": Client.COUNTRY_CHOICES,
                },
            )

        client = Client.objects.create(
            company_name=data["company_name"].strip(),
            kvk_number=kvk,
            sector=data["sector"],
            company_size=data["company_size"],
            country=data.get("country", "NL"),
            contact_person=data["contact_person"].strip(),
            email=data["email"].strip(),
            phone=data.get("phone", "").strip(),
            address=data["address"].strip(),
            city=data["city"].strip(),
            postal_code=data["postal_code"].strip(),
            account_manager=request.user if not request.user.is_superuser else None,
        )
        messages.success(request, f'Klant "{client.company_name}" aangemaakt')
        return redirect("dashboard:client_detail", pk=client.pk)


# TASK 3 — Client Edit View
class ClientUpdateView(LoginRequiredMixin, View):
    login_url = "/login/"

    def post(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        client.company_name = request.POST.get('company_name', client.company_name)
        client.sector = request.POST.get('sector', client.sector)
        client.company_size = request.POST.get('company_size', client.company_size)
        client.contact_person = request.POST.get('contact_person', client.contact_person)
        client.email = request.POST.get('email', client.email)
        client.country = request.POST.get('country', client.country)
        client.save()
        messages.success(request, 'Client bijgewerkt')
        return redirect('dashboard:client_detail', pk=pk)


# ─── Audits ────────────────────────────────────────────────────────────────────


# TASK 2 — New Audit View
class NewAuditView(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request):
        clients = Client.objects.all().order_by('company_name')
        selected_client_id = request.GET.get('client_id')
        return render(request, 'dashboard/audit_new.html', {
            'clients': clients,
            'tier_choices': ComplianceAudit.TIER_CHOICES,
            'selected_client_id': selected_client_id,
        })

    def post(self, request):
        client_id = request.POST.get('client')
        tier = request.POST.get('tier')
        quoted_price = request.POST.get('quoted_price')

        if not all([client_id, tier, quoted_price]):
            messages.error(request, 'Alle velden zijn verplicht')
            return redirect('dashboard:audit_new')

        try:
            audit = ComplianceAudit.objects.create(
                client_id=client_id,
                tier=tier,
                quoted_price=quoted_price,
                status='INTAKE',
            )
        except Exception as e:
            messages.error(request, f'Fout bij aanmaken audit: {e}')
            return redirect('dashboard:audit_new')

        messages.success(request, f'Audit aangemaakt voor {audit.client.company_name}')
        return redirect('dashboard:audit_detail', pk=audit.pk)


class AuditsView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/audits.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        qs = (
            ComplianceAudit.objects.all()
            if user.is_superuser
            else ComplianceAudit.objects.filter(client__account_manager=user)
        )
        status_filter = self.request.GET.get("status", "")
        tier_filter = self.request.GET.get("tier", "")
        if status_filter:
            qs = qs.filter(status=status_filter)
        if tier_filter:
            qs = qs.filter(tier=tier_filter)
        ctx["audits"] = qs.select_related("client").order_by("-created_at")
        ctx["current_status"] = status_filter
        ctx["current_tier"] = tier_filter
        ctx["status_choices"] = ComplianceAudit.STATUS_CHOICES
        ctx["tier_choices"] = ComplianceAudit.TIER_CHOICES
        ctx["total_audits"] = qs.count()
        return ctx


class AuditDetailView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/audit_detail.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        audit = get_object_or_404(ComplianceAudit, pk=kwargs["pk"])
        ctx["audit"] = audit
        ctx["client"] = audit.client
        ctx["tab"] = self.request.GET.get("tab", "overview")

        gaps = audit.gaps.all()
        ctx["gaps"] = gaps
        ctx["critical_gaps"] = gaps.filter(severity="CRITICAL", addressed=False).count()
        ctx["high_gaps"] = gaps.filter(severity="HIGH", addressed=False).count()
        ctx["medium_gaps"] = gaps.filter(severity="MEDIUM", addressed=False).count()
        ctx["low_gaps"] = gaps.filter(severity="LOW", addressed=False).count()

        # Category breakdown for heatmap
        cat_counts = gaps.values("category").annotate(n=Count("id")).order_by()
        ctx["gap_by_category"] = {r["category"]: r["n"] for r in cat_counts}
        ctx["max_cat_count"] = max(ctx["gap_by_category"].values(), default=1)

        ctx["total_effort"] = gaps.aggregate(s=Sum("estimated_effort_hours"))["s"] or 0
        ctx["total_cost"] = gaps.aggregate(s=Sum("estimated_cost_euros"))["s"] or 0
        documents = audit.documents.order_by("-uploaded_at")
        ctx["documents"] = documents

        # Task 7: Build timeline
        ctx["timeline_events"] = build_audit_timeline(audit, gaps, documents)

        # Valid transitions for current status
        ctx["valid_transitions"] = VALID_TRANSITIONS.get(audit.status, [])

        return ctx


# TASK 4 — Audit Status Transition
class AuditTransitionView(LoginRequiredMixin, View):
    login_url = "/login/"

    def post(self, request, pk):
        audit = get_object_or_404(ComplianceAudit, pk=pk)
        target_status = request.POST.get('status')

        if target_status not in VALID_TRANSITIONS.get(audit.status, []):
            messages.error(request, 'Ongeldige statusovergang')
            return redirect('dashboard:audit_detail', pk=pk)

        audit.status = target_status
        if target_status == 'DELIVERED':
            audit.delivered_at = timezone.now()
        if target_status == 'COMPLETE':
            audit.completed_at = timezone.now()
        audit.save()
        messages.success(request, f'Status bijgewerkt naar {target_status}')
        return redirect('dashboard:audit_detail', pk=pk)


# ─── Global Gap Browser ────────────────────────────────────────────────────────


class GapsView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/gaps.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        qs = (
            ComplianceGap.objects.all()
            if user.is_superuser
            else ComplianceGap.objects.filter(audit__client__account_manager=user)
        )
        ctx["total_gaps"] = qs.count()
        ctx["critical_open"] = qs.filter(severity="CRITICAL", addressed=False).count()
        ctx["avg_risk"] = round(
            float(qs.aggregate(avg=Avg("risk_score"))["avg"] or 0), 1
        )
        ctx["total_effort"] = qs.aggregate(s=Sum("estimated_effort_hours"))["s"] or 0

        # Category treemap data
        cat_data = (
            qs.values("category")
            .annotate(n=Count("id"), avg_risk=Avg("risk_score"))
            .order_by("-n")
        )
        ctx["treemap_data"] = list(cat_data)
        ctx["treemap_max"] = max((c["n"] for c in ctx["treemap_data"]), default=1)

        ctx["gaps"] = qs.select_related("audit__client").order_by(
            "-severity", "-risk_score"
        )[:100]
        ctx["severity_choices"] = ComplianceGap.SEVERITY_CHOICES
        ctx["category_choices"] = ComplianceGap.CATEGORY_CHOICES
        return ctx


# TASK 5 — Gap Mark-as-Addressed
class GapAddressView(LoginRequiredMixin, View):
    login_url = "/login/"

    def post(self, request, pk):
        gap = get_object_or_404(ComplianceGap, pk=pk)
        gap.addressed = True
        gap.addressed_date = timezone.now().date()
        gap.implementation_notes = request.POST.get('implementation_notes', '')
        gap.save()

        # Return updated row partial for HTMX swap
        return render(request,
            'dashboard/partials/gap_row.html',
            {'gap': gap})


# TASK 6 — Document Delete / Reprocess
class DocumentDeleteView(LoginRequiredMixin, View):
    login_url = "/login/"

    def post(self, request, pk):
        doc = get_object_or_404(ClientDocument, pk=pk)
        # Only allow delete if audit not PROCESSING
        if doc.audit.status == 'PROCESSING':
            messages.error(request,
                'Kan document niet verwijderen tijdens verwerking')
            return redirect('dashboard:audit_detail', pk=doc.audit.pk)
        audit_pk = doc.audit.pk
        filename = doc.original_filename
        doc.file.delete(save=False)
        doc.delete()
        messages.success(request, f'Document "{filename}" verwijderd')
        return redirect('dashboard:audit_detail', pk=audit_pk)


class DocumentReprocessView(LoginRequiredMixin, View):
    login_url = "/login/"

    def post(self, request, pk):
        doc = get_object_or_404(ClientDocument, pk=pk)
        # Reset processing state
        doc.processed = False
        doc.text_extracted = False
        doc.processing_error = ''
        doc.save(update_fields=['processed', 'text_extracted', 'processing_error'])

        def _extract(doc_id):
            try:
                from docling.document_converter import DocumentConverter
                d = ClientDocument.objects.get(pk=doc_id)
                converter = DocumentConverter()
                result = converter.convert(d.file.path)
                d.text_extracted = True
                d.processed = True
                d.save(update_fields=["text_extracted", "processed"])
                logger.info(f"Reprocessed {d.original_filename}")
            except Exception as e:
                logger.error(f"Reprocess error for {doc_id}: {e}")
                ClientDocument.objects.filter(pk=doc_id).update(
                    processing_error=str(e)
                )

        threading.Thread(target=_extract, args=(doc.pk,), daemon=True).start()
        messages.success(request, f'Document "{doc.original_filename}" wordt opnieuw verwerkt')
        return redirect('dashboard:audit_detail', pk=doc.audit.pk)


# ─── HTMX Partials ────────────────────────────────────────────────────────────


class HtmxAuditStatus(LoginRequiredMixin, View):
    """Polls every 3s while audit is PROCESSING or ANALYSIS."""
    login_url = "/login/"

    def get(self, request, pk):
        audit = get_object_or_404(ComplianceAudit, pk=pk)
        return render(request, "dashboard/partials/audit_status.html", {"audit": audit})


class HtmxGapRows(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request):
        audit_id = request.GET.get("audit_id")
        severity = request.GET.get("severity", "")
        category = request.GET.get("category", "")
        addressed = request.GET.get("addressed", "")
        search = request.GET.get("q", "")

        qs = ComplianceGap.objects.all()
        if audit_id:
            qs = qs.filter(audit_id=audit_id)
        if severity:
            qs = qs.filter(severity=severity)
        if category:
            qs = qs.filter(category=category)
        if addressed == "open":
            qs = qs.filter(addressed=False)
        elif addressed == "resolved":
            qs = qs.filter(addressed=True)
        if search:
            qs = qs.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        return render(
            request,
            "dashboard/partials/gap_rows.html",
            {
                "gaps": qs.select_related("audit__client").order_by(
                    "-severity", "-risk_score"
                ),
                "show_client": not bool(audit_id),
            },
        )


class HtmxClientSearch(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request):
        q = request.GET.get("q", "")
        sector = request.GET.get("sector", "")
        size = request.GET.get("size", "")
        user = request.user
        qs = (
            Client.objects.all()
            if user.is_superuser
            else Client.objects.filter(account_manager=user)
        )
        if q:
            qs = qs.filter(
                Q(company_name__icontains=q)
                | Q(kvk_number__icontains=q)
                | Q(contact_person__icontains=q)
            )
        if sector:
            qs = qs.filter(sector=sector)
        if size:
            qs = qs.filter(company_size=size)
        return render(
            request,
            "dashboard/partials/client_rows.html",
            {
                "clients": qs.prefetch_related("audits").order_by("company_name"),
            },
        )


class HtmxAuditRows(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request):
        user = request.user
        qs = (
            ComplianceAudit.objects.all()
            if user.is_superuser
            else ComplianceAudit.objects.filter(client__account_manager=user)
        )
        status_filter = request.GET.get("status", "")
        tier_filter = request.GET.get("tier", "")
        if status_filter:
            qs = qs.filter(status=status_filter)
        if tier_filter:
            qs = qs.filter(tier=tier_filter)
        return render(
            request,
            "dashboard/partials/audit_rows.html",
            {
                "audits": qs.select_related("client").order_by("-created_at"),
            },
        )
