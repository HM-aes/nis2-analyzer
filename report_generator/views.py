"""
Report Generator Views
- SectorReportFormView: Public-facing lead generation page (no login required)
- GapReportDownloadView: Download gap analysis PDF for completed audit
- GapReportGenerateView: HTMX trigger endpoint
"""

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.utils import timezone

from compliance_engine.models import ComplianceAudit, ComplianceGap, Client
from .generator import NIS2ReportGenerator


class SectorReportFormView(View):
    """
    Public-facing form: select sector and get a free sector requirements
    report PDF. Lead generation tool — no login required.
    """
    def get(self, request):
        sector_choices = Client.SECTOR_CHOICES
        country_choices = Client.COUNTRY_CHOICES
        return render(request, 'report_generator/sector_report.html', {
            'sector_choices': sector_choices,
            'country_choices': country_choices,
        })

    def post(self, request):
        company_name = request.POST.get('company_name', 'Your Organisation')
        sector = request.POST.get('sector', 'MSP')
        country = request.POST.get('country', 'NL')
        company_size = request.POST.get('company_size', 'MEDIUM')
        entity_type = request.POST.get('entity_type', 'IMPORTANT')
        email = request.POST.get('email', '')

        # Validate required fields
        if not company_name.strip():
            return render(request, 'report_generator/sector_report.html', {
                'sector_choices': Client.SECTOR_CHOICES,
                'country_choices': Client.COUNTRY_CHOICES,
                'error': 'Bedrijfsnaam is verplicht.',
                'data': request.POST,
            })

        try:
            generator = NIS2ReportGenerator()
            pdf_bytes = generator.generate_sector_report(
                company_name=company_name,
                sector=sector,
                country=country,
                company_size=company_size,
                entity_type=entity_type,
            )
        except Exception as e:
            return render(request, 'report_generator/sector_report.html', {
                'sector_choices': Client.SECTOR_CHOICES,
                'country_choices': Client.COUNTRY_CHOICES,
                'error': f'Fout bij het genereren van het rapport: {str(e)}',
                'data': request.POST,
            })

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = (
            f'NIS2-Sector-Report-{sector}-'
            f'{timezone.now().strftime("%Y%m%d")}.pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class GapReportDownloadView(LoginRequiredMixin, View):
    """
    Download gap analysis PDF report for a completed audit.
    Shows download button when gaps exist — no gate on report_generated flag.
    """
    login_url = '/login/'

    def get(self, request, pk):
        audit = get_object_or_404(ComplianceAudit, pk=pk)
        client = audit.client
        gaps = ComplianceGap.objects.filter(audit=audit)

        if not gaps.exists():
            messages.error(request, 'Geen gaps gevonden voor dit audit')
            return redirect('dashboard:audit_detail', pk=pk)

        try:
            generator = NIS2ReportGenerator()
            pdf_bytes = generator.generate_gap_report(
                audit=audit,
                gaps=gaps,
                client=client,
            )
        except Exception as e:
            messages.error(request, f'Fout bij het genereren van het rapport: {str(e)}')
            return redirect('dashboard:audit_detail', pk=pk)

        # Mark report as generated
        audit.report_generated = True
        audit.report_generated_at = timezone.now()
        audit.save(update_fields=['report_generated', 'report_generated_at'])

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        safe_name = client.company_name.replace(' ', '-').replace('/', '-')
        filename = (
            f'NIS2-Gap-Analysis-{safe_name}-'
            f'{timezone.now().strftime("%Y%m%d")}.pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class GapReportGenerateView(LoginRequiredMixin, View):
    """
    HTMX endpoint: trigger report generation status check.
    Returns JSON with download URL when ready.
    """
    login_url = '/login/'

    def post(self, request, pk):
        audit = get_object_or_404(ComplianceAudit, pk=pk)
        gaps_count = audit.gaps.count()
        if gaps_count > 0:
            return JsonResponse({
                'status': 'ready',
                'download_url': f'/reports/audit/{pk}/download/',
                'gaps_count': gaps_count,
            })
        return JsonResponse({
            'status': 'no_gaps',
            'message': 'Geen gaps gevonden. Voer eerst een AI analyse uit.',
        })
