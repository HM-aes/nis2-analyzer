"""
NIS2 Dashboard Test Suite — covers all 18 PRD tasks.
Tests are self-contained (no external services needed).
"""

import uuid
from django.test import TestCase, Client as TestClient
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from compliance_engine.models import (
    Client,
    ComplianceAudit,
    ComplianceGap,
    ClientDocument,
)


# ─── Shared Fixtures ──────────────────────────────────────────────────────────

def make_user(username='consultant', is_super=False):
    u = User.objects.create_user(username=username, password='testpass123')
    if is_super:
        u.is_superuser = True
        u.is_staff = True
        u.save()
    return u


def make_client(user=None, **kwargs):
    defaults = dict(
        company_name='Acme BV',
        kvk_number=str(uuid.uuid4().int)[:8],
        sector='MSP',
        company_size='MEDIUM',
        country='NL',
        contact_person='Jan Jansen',
        email='jan@acme.nl',
        address='Teststraat 1',
        city='Amsterdam',
        postal_code='1234 AB',
        account_manager=user,
    )
    defaults.update(kwargs)
    return Client.objects.create(**defaults)


def make_audit(client, **kwargs):
    defaults = dict(
        tier='T1',
        quoted_price=950,
        status='INTAKE',
    )
    defaults.update(kwargs)
    return ComplianceAudit.objects.create(client=client, **defaults)


def make_gap(audit, **kwargs):
    defaults = dict(
        category='TECHNICAL',
        severity='HIGH',
        title='Missing MFA',
        description='No MFA configured',
        nis2_article='Article 21.2',
        nis2_requirement='Implement MFA',
        current_state='No MFA',
        required_state='MFA required',
        recommendation='Deploy MFA',
        estimated_effort_hours=8,
        risk_score=7,
    )
    defaults.update(kwargs)
    return ComplianceGap.objects.create(audit=audit, **defaults)


# ─── Task 1: Country Field ─────────────────────────────────────────────────────

class Task1CountryFieldTest(TestCase):
    def test_client_has_country_field(self):
        user = make_user()
        client = make_client(user=user, country='DE')
        self.assertEqual(client.country, 'DE')

    def test_country_defaults_to_nl(self):
        user = make_user()
        client = make_client(user=user)
        self.assertEqual(client.country, 'NL')

    def test_country_choices_include_expected(self):
        codes = [c[0] for c in Client.COUNTRY_CHOICES]
        for expected in ['NL', 'DE', 'BE', 'FR', 'GB']:
            self.assertIn(expected, codes)

    def test_client_new_renders_country_dropdown(self):
        u = make_user()
        tc = TestClient()
        tc.login(username='consultant', password='testpass123')
        resp = tc.get(reverse('dashboard:client_new'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'country')
        self.assertContains(resp, 'Netherlands')

    def test_client_detail_shows_country(self):
        u = make_user()
        c = make_client(user=u, country='BE')
        tc = TestClient()
        tc.login(username='consultant', password='testpass123')
        resp = tc.get(reverse('dashboard:client_detail', kwargs={'pk': c.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Belgium')


# ─── Task 2: Audit Creation View ───────────────────────────────────────────────

class Task2NewAuditViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client_obj = make_client(user=self.user)
        self.tc = TestClient()
        self.tc.login(username='consultant', password='testpass123')

    def test_get_renders_form(self):
        resp = self.tc.get(reverse('dashboard:audit_new'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Nieuwe Audit')

    def test_get_preselects_client_from_query_param(self):
        resp = self.tc.get(
            reverse('dashboard:audit_new'),
            {'client_id': str(self.client_obj.pk)}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'selected')

    def test_post_creates_audit_and_redirects(self):
        resp = self.tc.post(reverse('dashboard:audit_new'), {
            'client': str(self.client_obj.pk),
            'tier': 'T1',
            'quoted_price': '950',
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(ComplianceAudit.objects.filter(
            client=self.client_obj, tier='T1', status='INTAKE').exists())

    def test_post_missing_fields_redirects_with_error(self):
        initial_count = ComplianceAudit.objects.count()
        resp = self.tc.post(reverse('dashboard:audit_new'), {
            'client': str(self.client_obj.pk),
            # missing tier and quoted_price
        }, follow=True)
        self.assertEqual(ComplianceAudit.objects.count(), initial_count)

    def test_tier_choices_in_context(self):
        resp = self.tc.get(reverse('dashboard:audit_new'))
        self.assertIn('tier_choices', resp.context)

    def test_audit_new_url_exists(self):
        url = reverse('dashboard:audit_new')
        self.assertEqual(url, '/dashboard/audits/new/')


# ─── Task 3: Client Edit View ───────────────────────────────────────────────────

class Task3ClientUpdateViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client_obj = make_client(user=self.user, company_name='Old Name')
        self.tc = TestClient()
        self.tc.login(username='consultant', password='testpass123')

    def test_post_updates_client_fields(self):
        resp = self.tc.post(
            reverse('dashboard:client_update', kwargs={'pk': self.client_obj.pk}),
            {
                'company_name': 'New Name',
                'sector': 'CLOUD',
                'company_size': 'LARGE',
                'contact_person': 'Piet',
                'email': 'piet@new.nl',
                'country': 'DE',
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.client_obj.refresh_from_db()
        self.assertEqual(self.client_obj.company_name, 'New Name')
        self.assertEqual(self.client_obj.country, 'DE')
        self.assertEqual(self.client_obj.sector, 'CLOUD')

    def test_client_detail_shows_edit_form(self):
        resp = self.tc.get(reverse('dashboard:client_detail', kwargs={'pk': self.client_obj.pk}))
        # The edit form POSTs to /dashboard/clients/<pk>/edit/
        self.assertContains(resp, '/edit/')

    def test_kvk_not_editable_in_form(self):
        resp = self.tc.get(reverse('dashboard:client_detail', kwargs={'pk': self.client_obj.pk}))
        self.assertContains(resp, 'KVK')
        self.assertContains(resp, 'disabled')

    def test_url_exists(self):
        url = reverse('dashboard:client_update', kwargs={'pk': self.client_obj.pk})
        self.assertIn('/edit/', url)


# ─── Task 4: Audit Status Transitions ──────────────────────────────────────────

class Task4AuditTransitionTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client_obj = make_client(user=self.user)
        self.tc = TestClient()
        self.tc.login(username='consultant', password='testpass123')

    def test_review_to_complete(self):
        audit = make_audit(self.client_obj, status='REVIEW')
        self.tc.post(
            reverse('dashboard:audit_transition', kwargs={'pk': audit.pk}),
            {'status': 'COMPLETE'},
        )
        audit.refresh_from_db()
        self.assertEqual(audit.status, 'COMPLETE')
        self.assertIsNotNone(audit.completed_at)

    def test_complete_to_delivered(self):
        audit = make_audit(self.client_obj, status='COMPLETE')
        self.tc.post(
            reverse('dashboard:audit_transition', kwargs={'pk': audit.pk}),
            {'status': 'DELIVERED'},
        )
        audit.refresh_from_db()
        self.assertEqual(audit.status, 'DELIVERED')
        self.assertIsNotNone(audit.delivered_at)

    def test_invalid_transition_rejected(self):
        audit = make_audit(self.client_obj, status='DELIVERED')
        self.tc.post(
            reverse('dashboard:audit_transition', kwargs={'pk': audit.pk}),
            {'status': 'INTAKE'},
        )
        audit.refresh_from_db()
        self.assertEqual(audit.status, 'DELIVERED')  # unchanged

    def test_error_to_intake(self):
        audit = make_audit(self.client_obj, status='ERROR')
        self.tc.post(
            reverse('dashboard:audit_transition', kwargs={'pk': audit.pk}),
            {'status': 'INTAKE'},
        )
        audit.refresh_from_db()
        self.assertEqual(audit.status, 'INTAKE')

    def test_transition_buttons_in_review_template(self):
        audit = make_audit(self.client_obj, status='REVIEW')
        resp = self.tc.get(reverse('dashboard:audit_detail', kwargs={'pk': audit.pk}))
        self.assertContains(resp, 'Analyse Goedkeuren')
        self.assertContains(resp, 'Opnieuw Starten')

    def test_transition_buttons_in_complete_template(self):
        audit = make_audit(self.client_obj, status='COMPLETE')
        resp = self.tc.get(reverse('dashboard:audit_detail', kwargs={'pk': audit.pk}))
        self.assertContains(resp, 'Rapport Geleverd')


# ─── Task 5: Gap Mark-as-Addressed ─────────────────────────────────────────────

class Task5GapAddressViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client_obj = make_client(user=self.user)
        self.audit = make_audit(self.client_obj)
        self.gap = make_gap(self.audit)
        self.tc = TestClient()
        self.tc.login(username='consultant', password='testpass123')

    def test_post_marks_gap_addressed(self):
        self.tc.post(
            reverse('dashboard:gap_address', kwargs={'pk': self.gap.pk}),
            {'implementation_notes': 'Deployed MFA via Azure AD'},
        )
        self.gap.refresh_from_db()
        self.assertTrue(self.gap.addressed)
        self.assertIsNotNone(self.gap.addressed_date)
        self.assertEqual(self.gap.implementation_notes, 'Deployed MFA via Azure AD')

    def test_post_returns_partial_html(self):
        resp = self.tc.post(
            reverse('dashboard:gap_address', kwargs={'pk': self.gap.pk}),
            {'implementation_notes': 'Done'},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Opgelost')

    def test_gap_address_url_exists(self):
        url = reverse('dashboard:gap_address', kwargs={'pk': self.gap.pk})
        self.assertIn('/address/', url)

    def test_mark_as_addressed_form_in_audit_detail(self):
        resp = self.tc.get(reverse('dashboard:audit_detail', kwargs={'pk': self.audit.pk}))
        # The HTMX form posts to /dashboard/gaps/<pk>/address/
        self.assertContains(resp, '/address/')
        self.assertContains(resp, 'Markeer als Opgelost')


# ─── Task 6: Document Delete / Reprocess ───────────────────────────────────────

class Task6DocumentViewsTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client_obj = make_client(user=self.user)
        self.audit = make_audit(self.client_obj, status='INTAKE')
        self.tc = TestClient()
        self.tc.login(username='consultant', password='testpass123')

    def _make_doc(self):
        import tempfile, os
        from django.core.files.uploadedfile import SimpleUploadedFile
        f = SimpleUploadedFile('test.txt', b'NIS2 content', content_type='text/plain')
        return ClientDocument.objects.create(
            audit=self.audit,
            document_type='POLICY',
            file=f,
            original_filename='test.txt',
            file_size_bytes=12,
            uploaded_by=self.user,
        )

    def test_delete_removes_document(self):
        doc = self._make_doc()
        doc_pk = doc.pk
        self.tc.post(reverse('dashboard:document_delete', kwargs={'pk': doc_pk}))
        self.assertFalse(ClientDocument.objects.filter(pk=doc_pk).exists())

    def test_cannot_delete_during_processing(self):
        self.audit.status = 'PROCESSING'
        self.audit.save()
        doc = self._make_doc()
        self.tc.post(reverse('dashboard:document_delete', kwargs={'pk': doc.pk}))
        self.assertTrue(ClientDocument.objects.filter(pk=doc.pk).exists())

    def test_document_tab_rendered_in_audit_detail(self):
        resp = self.tc.get(reverse('dashboard:audit_detail', kwargs={'pk': self.audit.pk}))
        self.assertContains(resp, 'Documenten')

    def test_document_delete_url_exists(self):
        doc = self._make_doc()
        url = reverse('dashboard:document_delete', kwargs={'pk': doc.pk})
        self.assertIn('/delete/', url)


# ─── Task 7: Timeline Tab ──────────────────────────────────────────────────────

class Task7TimelineTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client_obj = make_client(user=self.user)
        self.audit = make_audit(self.client_obj, status='COMPLETE',
                                completed_at=timezone.now())
        self.tc = TestClient()
        self.tc.login(username='consultant', password='testpass123')

    def test_timeline_in_context(self):
        resp = self.tc.get(reverse('dashboard:audit_detail', kwargs={'pk': self.audit.pk}))
        self.assertIn('timeline_events', resp.context)
        events = resp.context['timeline_events']
        self.assertTrue(len(events) >= 1)

    def test_created_event_always_present(self):
        resp = self.tc.get(reverse('dashboard:audit_detail', kwargs={'pk': self.audit.pk}))
        events = resp.context['timeline_events']
        types = [e['type'] for e in events]
        self.assertIn('created', types)

    def test_completed_event_when_completed_at_set(self):
        resp = self.tc.get(reverse('dashboard:audit_detail', kwargs={'pk': self.audit.pk}))
        events = resp.context['timeline_events']
        types = [e['type'] for e in events]
        self.assertIn('completed', types)

    def test_timeline_tab_renders_in_template(self):
        resp = self.tc.get(reverse('dashboard:audit_detail', kwargs={'pk': self.audit.pk}))
        self.assertContains(resp, 'Timeline')
        self.assertContains(resp, 'Audit Tijdlijn')


# ─── Task 8–12: Report Generator App ──────────────────────────────────────────

class Task8ReportAppTest(TestCase):
    def test_report_generator_urls_registered(self):
        url = reverse('report_generator:sector_report')
        self.assertEqual(url, '/reports/sector/')

    def test_gap_report_download_url_registered(self):
        pk = uuid.uuid4()
        url = reverse('report_generator:gap_report_download', kwargs={'pk': pk})
        self.assertIn('/reports/audit/', url)
        self.assertIn('/download/', url)

    def test_sector_report_form_get(self):
        tc = TestClient()
        resp = tc.get(reverse('report_generator:sector_report'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'NIS2')

    def test_gap_report_download_requires_auth(self):
        pk = uuid.uuid4()
        tc = TestClient()
        resp = tc.get(
            reverse('report_generator:gap_report_download', kwargs={'pk': pk})
        )
        self.assertIn(resp.status_code, [302, 403])

    def test_generator_importable(self):
        from report_generator.generator import NIS2ReportGenerator
        self.assertTrue(callable(NIS2ReportGenerator))

    def test_charts_importable(self):
        from report_generator.charts import (
            compliance_gauge_image,
            severity_bar_chart_image,
            category_heatmap_image,
            remediation_timeline_image,
            png_to_reportlab_image,
        )
        for fn in [compliance_gauge_image, severity_bar_chart_image,
                   category_heatmap_image, remediation_timeline_image,
                   png_to_reportlab_image]:
            self.assertTrue(callable(fn))

    def test_claude_prompts_importable(self):
        from report_generator.claude_prompts import (
            SECTOR_REPORT_SYSTEM,
            SECTOR_REQUIREMENTS_PROMPT,
            EXECUTIVE_SUMMARY_PROMPT,
            REMEDIATION_ROADMAP_PROMPT,
            GAP_NARRATIVE_PROMPT,
            FINE_EXPOSURE_PROMPT,
        )
        for prompt in [SECTOR_REPORT_SYSTEM, SECTOR_REQUIREMENTS_PROMPT,
                       EXECUTIVE_SUMMARY_PROMPT, REMEDIATION_ROADMAP_PROMPT,
                       GAP_NARRATIVE_PROMPT, FINE_EXPOSURE_PROMPT]:
            self.assertIsInstance(prompt, str)
            self.assertTrue(len(prompt) > 10)


# ─── Task 13: Sector Report Form Template ──────────────────────────────────────

class Task13SectorReportFormTest(TestCase):
    def test_form_renders_all_fields(self):
        tc = TestClient()
        resp = tc.get(reverse('report_generator:sector_report'))
        self.assertEqual(resp.status_code, 200)
        for field in ['company_name', 'email', 'sector', 'country', 'company_size', 'entity_type']:
            self.assertContains(resp, field)

    def test_form_has_sector_choices(self):
        tc = TestClient()
        resp = tc.get(reverse('report_generator:sector_report'))
        self.assertContains(resp, 'Managed Service Provider')

    def test_form_has_country_choices(self):
        tc = TestClient()
        resp = tc.get(reverse('report_generator:sector_report'))
        self.assertContains(resp, 'Netherlands')

    def test_form_has_submit_button(self):
        tc = TestClient()
        resp = tc.get(reverse('report_generator:sector_report'))
        self.assertContains(resp, 'submit')


# ─── Task 14: Toast Notification System ────────────────────────────────────────

class Task14ToastSystemTest(TestCase):
    def test_base_template_has_toast_container(self):
        u = make_user()
        tc = TestClient()
        tc.login(username='consultant', password='testpass123')
        resp = tc.get(reverse('dashboard:home'))
        self.assertContains(resp, 'toastSystem')
        self.assertContains(resp, 'toast-container')

    def test_toast_fires_after_create_client(self):
        u = make_user()
        tc = TestClient()
        tc.login(username='consultant', password='testpass123')
        resp = tc.post(reverse('dashboard:client_new'), {
            'company_name': 'Toast Test BV',
            'kvk_number': '87654321',
            'sector': 'MSP',
            'company_size': 'SMALL',
            'country': 'NL',
            'contact_person': 'Test Persoon',
            'email': 'test@toast.nl',
            'address': 'Toaststraat 1',
            'city': 'Utrecht',
            'postal_code': '3512 AB',
        }, follow=True)
        self.assertContains(resp, 'aangemaakt')


# ─── Task 15: Loading States ────────────────────────────────────────────────────

class Task15LoadingStatesTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client_obj = make_client(user=self.user)
        self.tc = TestClient()
        self.tc.login(username='consultant', password='testpass123')

    def test_ai_analyse_button_has_spinner(self):
        audit = make_audit(self.client_obj, status='INTAKE')
        # Need at least one doc for the button to show
        from django.core.files.uploadedfile import SimpleUploadedFile
        ClientDocument.objects.create(
            audit=audit,
            document_type='POLICY',
            file=SimpleUploadedFile('x.txt', b'x'),
            original_filename='x.txt',
            file_size_bytes=1,
            uploaded_by=self.user,
        )
        resp = self.tc.get(reverse('dashboard:audit_detail', kwargs={'pk': audit.pk}))
        self.assertContains(resp, 'animate-spin')

    def test_audit_new_submit_has_loading_state(self):
        resp = self.tc.get(reverse('dashboard:audit_new'))
        self.assertContains(resp, 'running')
        self.assertContains(resp, 'Aanmaken...')


# ─── Task 16: Empty State CTAs ─────────────────────────────────────────────────

class Task16EmptyStatesTest(TestCase):
    def setUp(self):
        self.user = make_user(is_super=True)
        self.tc = TestClient()
        self.tc.login(username='consultant', password='testpass123')

    def test_dashboard_has_onboarding_cta_when_no_clients(self):
        resp = self.tc.get(reverse('dashboard:home'))
        self.assertContains(resp, 'Welkom bij NIS2 Analyzer')
        self.assertContains(resp, 'Eerste Klant Toevoegen')

    def test_clients_has_empty_state(self):
        resp = self.tc.get(reverse('dashboard:clients'))
        self.assertContains(resp, 'Voeg uw eerste klant')

    def test_audits_has_empty_state(self):
        resp = self.tc.get(reverse('dashboard:audits'))
        self.assertContains(resp, 'Nog geen audits')
        self.assertContains(resp, 'Eerste Audit Aanmaken')

    def test_gaps_has_empty_state(self):
        resp = self.tc.get(reverse('dashboard:gaps'))
        self.assertContains(resp, 'Nog geen gaps gevonden')
        self.assertContains(resp, 'Nieuwe Audit Starten')


# ─── Task 17: report_generated Pipeline Hook ───────────────────────────────────

class Task17ReportGeneratedTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client_obj = make_client(user=self.user)
        self.tc = TestClient()
        self.tc.login(username='consultant', password='testpass123')

    def test_download_button_shows_when_gaps_exist(self):
        audit = make_audit(self.client_obj, status='COMPLETE',
                           compliance_score=72)
        make_gap(audit)
        resp = self.tc.get(reverse('dashboard:audit_detail', kwargs={'pk': audit.pk}))
        # The download button links to /reports/audit/<pk>/download/
        self.assertContains(resp, '/reports/audit/')
        self.assertContains(resp, 'Rapport Downloaden')

    def test_download_button_absent_with_no_gaps(self):
        audit = make_audit(self.client_obj, status='INTAKE')
        resp = self.tc.get(reverse('dashboard:audit_detail', kwargs={'pk': audit.pk}))
        self.assertNotContains(resp, 'Rapport Downloaden')

    def test_gap_report_redirects_when_no_gaps(self):
        audit = make_audit(self.client_obj, status='COMPLETE')
        resp = self.tc.get(
            reverse('report_generator:gap_report_download', kwargs={'pk': audit.pk}),
            follow=True,
        )
        self.assertContains(resp, 'Geen gaps')


# ─── Task 18: Sidebar Navigation ───────────────────────────────────────────────

class Task18SidebarNavTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tc = TestClient()
        self.tc.login(username='consultant', password='testpass123')

    def test_sidebar_has_rapporten_section(self):
        resp = self.tc.get(reverse('dashboard:home'))
        self.assertContains(resp, 'Rapporten')

    def test_sidebar_has_sector_report_link(self):
        resp = self.tc.get(reverse('dashboard:home'))
        self.assertContains(resp, reverse('report_generator:sector_report'))

    def test_sidebar_has_audit_rapporten_link(self):
        resp = self.tc.get(reverse('dashboard:home'))
        self.assertContains(resp, reverse('dashboard:audits'))

    def test_sector_report_link_in_sidebar_text(self):
        resp = self.tc.get(reverse('dashboard:home'))
        self.assertContains(resp, 'Sector Rapport')


# ─── URL Routing Smoke Tests ────────────────────────────────────────────────────

class URLRoutingTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client_obj = make_client(user=self.user)
        self.audit = make_audit(self.client_obj)
        self.gap = make_gap(self.audit)
        self.tc = TestClient()
        self.tc.login(username='consultant', password='testpass123')

    def test_all_dashboard_urls_resolve(self):
        # Only test GET-accessible URLs (client_update is POST-only)
        urls = [
            reverse('dashboard:home'),
            reverse('dashboard:clients'),
            reverse('dashboard:client_new'),
            reverse('dashboard:client_detail', kwargs={'pk': self.client_obj.pk}),
            reverse('dashboard:audits'),
            reverse('dashboard:audit_new'),
            reverse('dashboard:audit_detail', kwargs={'pk': self.audit.pk}),
        ]
        for url in urls:
            resp = self.tc.get(url)
            self.assertIn(resp.status_code, [200, 302],
                          msg=f'{url} returned {resp.status_code}')

    def test_client_update_url_accepts_post(self):
        resp = self.tc.post(
            reverse('dashboard:client_update', kwargs={'pk': self.client_obj.pk}),
            {'company_name': 'Updated', 'sector': 'MSP',
             'company_size': 'MEDIUM', 'contact_person': 'Test',
             'email': 'test@test.nl', 'country': 'NL'},
        )
        self.assertIn(resp.status_code, [200, 302])

    def test_report_generator_urls_resolve(self):
        resp = self.tc.get(reverse('report_generator:sector_report'))
        self.assertEqual(resp.status_code, 200)

    def test_login_required_on_protected_views(self):
        anon = TestClient()
        protected = [
            reverse('dashboard:home'),
            reverse('dashboard:clients'),
            reverse('dashboard:audits'),
            reverse('dashboard:gaps'),
        ]
        for url in protected:
            resp = anon.get(url)
            self.assertEqual(resp.status_code, 302,
                             msg=f'{url} should require login')

    def test_sector_report_is_public(self):
        anon = TestClient()
        resp = anon.get(reverse('report_generator:sector_report'))
        self.assertEqual(resp.status_code, 200)
