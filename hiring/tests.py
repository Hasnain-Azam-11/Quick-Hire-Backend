from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from Client.models import ClientProfile, JobPost
from worker.models import WorkerBio, WorkerService
from .models import Deal, Offer


class HiringWorkflowTests(APITestCase):
    """
    Tests covering:
      - Full Happy Path A (JobPost -> Worker applies -> counter-offer -> accept -> complete)
      - Full Happy Path B (WorkerService -> Client hires -> counter-offer -> accept -> complete)
      - All 9 Business Rules + 'my deals' filtering (?role=client|worker, ?status=...)
    """

    def setUp(self):
        # 1. Client user (has ClientProfile)
        self.client_user = User.objects.create_user(
            username='alice_client',
            email='alice@example.com',
            password='password123',
        )
        self.client_profile = ClientProfile.objects.create(user=self.client_user)

        # 2. Worker user (has ClientProfile + WorkerBio, so can act as worker OR client)
        self.worker_user = User.objects.create_user(
            username='bob_worker',
            email='bob@example.com',
            password='password123',
        )
        self.worker_client_profile = ClientProfile.objects.create(user=self.worker_user)
        self.worker_bio = WorkerBio.objects.create(
            client_profile=self.worker_client_profile,
            cnic='12345-1234567-1',
            age=28,
            years_of_experience=4,
            expertise_categories='handyman',
            gender='M',
        )

        # 3. Outsider user (3rd party who is not part of Alice & Bob's deals)
        self.outsider_user = User.objects.create_user(
            username='mallory_outsider',
            email='mallory@example.com',
            password='password123',
        )
        self.outsider_client_profile = ClientProfile.objects.create(user=self.outsider_user)
        self.outsider_worker_bio = WorkerBio.objects.create(
            client_profile=self.outsider_client_profile,
            cnic='99999-9999999-9',
            age=30,
            years_of_experience=2,
            expertise_categories='cleaning',
            gender='F',
        )

        # Open JobPost by Alice (Path A target)
        self.job_post = JobPost.objects.create(
            client=self.client_profile,
            title='Fix kitchen cabinets',
            job_description='Repair hinges and align doors',
            city='Lahore',
            area='DHA',
            category='handyman',
            duration_unit='day',
            duration='2 days',
            start_date=date.today() + timedelta(days=2),
            status='open',
        )

        # Available WorkerService by Bob (Path B target)
        self.worker_service = WorkerService.objects.create(
            worker=self.worker_bio,
            category='handyman',
            job_description='Professional carpentry and handyman work',
            city='Lahore',
            area='Gulberg',
            rate=Decimal('2000.00'),
            price_unit='day',
            is_available=True,
        )

    def test_happy_path_a_job_post_application_flow(self):
        """Path A: Client posts JobPost -> Worker applies -> Client counters -> Worker accepts -> Client completes."""
        # Step 1: Bob (worker) applies to Alice's JobPost with an opening offer of 1800/day
        self.client.force_authenticate(user=self.worker_user)
        create_res = self.client.post(
            '/hiring/deals/',
            {
                'job_post': self.job_post.id,
                'price': '1800.00',
                'price_unit': 'day',
                'message': 'I can start on schedule.',
            },
            format='json',
        )
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        deal_id = create_res.data['id']
        self.assertEqual(create_res.data['initiated_by'], 'worker')
        self.assertEqual(create_res.data['status'], 'negotiating')
        self.assertEqual(len(create_res.data['offers']), 1)

        # Step 2: Alice (client) sends a counter-offer of 1500/day
        self.client.force_authenticate(user=self.client_user)
        counter_res = self.client.post(
            f'/hiring/deals/{deal_id}/offers/',
            {
                'price': '1500.00',
                'price_unit': 'day',
                'message': 'Can you do 1500 per day?',
            },
            format='json',
        )
        self.assertEqual(counter_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(counter_res.data['sender'], 'client')

        # Step 3: Bob (worker) accepts Alice's counter-offer
        self.client.force_authenticate(user=self.worker_user)
        accept_res = self.client.post(f'/hiring/deals/{deal_id}/accept/')
        self.assertEqual(accept_res.status_code, status.HTTP_200_OK)
        self.assertEqual(accept_res.data['status'], 'agreed')
        self.assertEqual(Decimal(accept_res.data['agreed_price']), Decimal('1500.00'))
        self.assertEqual(accept_res.data['price_unit'], 'day')
        self.job_post.refresh_from_db()
        self.assertEqual(self.job_post.status, 'assigned')

        # Step 4: Alice (client) marks the deal completed
        self.client.force_authenticate(user=self.client_user)
        complete_res = self.client.post(f'/hiring/deals/{deal_id}/complete/')
        self.assertEqual(complete_res.status_code, status.HTTP_200_OK)
        self.assertEqual(complete_res.data['status'], 'completed')
        self.assertIsNotNone(complete_res.data['completed_at'])
        self.job_post.refresh_from_db()
        self.assertEqual(self.job_post.status, 'completed')

    def test_happy_path_b_worker_service_hire_flow(self):
        """Path B: Worker posts WorkerService -> Client sends hire request -> Worker counters -> Client accepts -> Client completes."""
        # Step 1: Alice (client) sends a hire request for Bob's WorkerService at 1600/day
        self.client.force_authenticate(user=self.client_user)
        create_res = self.client.post(
            '/hiring/deals/',
            {
                'worker_service': self.worker_service.id,
                'price': '1600.00',
                'price_unit': 'day',
                'message': 'Need carpentry work at my house.',
            },
            format='json',
        )
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        deal_id = create_res.data['id']
        self.assertEqual(create_res.data['initiated_by'], 'client')
        self.assertEqual(create_res.data['status'], 'negotiating')

        # Step 2: Bob (worker) sends a counter-offer of 1900/day
        self.client.force_authenticate(user=self.worker_user)
        counter_res = self.client.post(
            f'/hiring/deals/{deal_id}/offers/',
            {
                'price': '1900.00',
                'price_unit': 'day',
                'message': 'My best rate is 1900/day including tools.',
            },
            format='json',
        )
        self.assertEqual(counter_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(counter_res.data['sender'], 'worker')

        # Step 3: Alice (client) accepts Bob's counter-offer
        self.client.force_authenticate(user=self.client_user)
        accept_res = self.client.post(f'/hiring/deals/{deal_id}/accept/')
        self.assertEqual(accept_res.status_code, status.HTTP_200_OK)
        self.assertEqual(accept_res.data['status'], 'agreed')
        self.assertEqual(Decimal(accept_res.data['agreed_price']), Decimal('1900.00'))

        # Step 4: Alice (client) marks the deal completed
        complete_res = self.client.post(f'/hiring/deals/{deal_id}/complete/')
        self.assertEqual(complete_res.status_code, status.HTTP_200_OK)
        self.assertEqual(complete_res.data['status'], 'completed')

    def test_rule_1_cannot_accept_own_offer(self):
        """Rule #1: You cannot accept your own offer; only the other party's latest pending offer can be accepted."""
        # Bob (worker) creates a deal (so Bob is the sender of the opening offer)
        self.client.force_authenticate(user=self.worker_user)
        res = self.client.post(
            '/hiring/deals/',
            {'job_post': self.job_post.id, 'price': '1800.00', 'price_unit': 'day'},
            format='json',
        )
        deal_id = res.data['id']

        # Bob tries to accept his own opening offer -> must fail with 400
        self_accept_res = self.client.post(f'/hiring/deals/{deal_id}/accept/')
        self.assertEqual(self_accept_res.status_code, status.HTTP_400_BAD_REQUEST)

        # Alice counters (now Alice is the sender of the pending offer)
        self.client.force_authenticate(user=self.client_user)
        self.client.post(
            f'/hiring/deals/{deal_id}/offers/',
            {'price': '1500.00', 'price_unit': 'day'},
            format='json',
        )

        # Alice tries to accept her own counter-offer -> must fail with 400
        client_self_accept = self.client.post(f'/hiring/deals/{deal_id}/accept/')
        self.assertEqual(client_self_accept.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rule_2_counter_offer_supersedes_previous_pending_offer(self):
        """Rule #2: A new counter-offer marks the previous pending offer as superseded."""
        self.client.force_authenticate(user=self.worker_user)
        res = self.client.post(
            '/hiring/deals/',
            {'job_post': self.job_post.id, 'price': '2000.00', 'price_unit': 'day'},
            format='json',
        )
        deal_id = res.data['id']
        first_offer_id = res.data['offers'][0]['id']

        # Alice sends a counter-offer
        self.client.force_authenticate(user=self.client_user)
        second_res = self.client.post(
            f'/hiring/deals/{deal_id}/offers/',
            {'price': '1600.00', 'price_unit': 'day'},
            format='json',
        )
        second_offer_id = second_res.data['id']

        self.assertEqual(Offer.objects.get(id=first_offer_id).status, 'superseded')
        self.assertEqual(Offer.objects.get(id=second_offer_id).status, 'pending')
        self.assertEqual(Offer.objects.filter(deal_id=deal_id, status='pending').count(), 1)

    def test_rule_3_accepting_offer_sets_deal_fields_and_assigns_job_post(self):
        """Rule #3: Accepting an offer sets agreed_price, price_unit, status=agreed, agreed_at, and JobPost.status=assigned."""
        self.client.force_authenticate(user=self.worker_user)
        res = self.client.post(
            '/hiring/deals/',
            {'job_post': self.job_post.id, 'price': '1750.00', 'price_unit': 'day'},
            format='json',
        )
        deal_id = res.data['id']

        self.client.force_authenticate(user=self.client_user)
        accept_res = self.client.post(f'/hiring/deals/{deal_id}/accept/')
        self.assertEqual(accept_res.status_code, status.HTTP_200_OK)

        deal = Deal.objects.get(id=deal_id)
        self.assertEqual(deal.status, 'agreed')
        self.assertEqual(deal.agreed_price, Decimal('1750.00'))
        self.assertEqual(deal.price_unit, 'day')
        self.assertIsNotNone(deal.agreed_at)

        self.job_post.refresh_from_db()
        self.assertEqual(self.job_post.status, 'assigned')

    def test_rule_4_only_one_active_deal_per_pair(self):
        """Rule #4: Only one active Deal per (job_post, worker) or (worker_service, client)."""
        # Path A duplicate check
        self.client.force_authenticate(user=self.worker_user)
        first_a = self.client.post(
            '/hiring/deals/',
            {'job_post': self.job_post.id, 'price': '1800.00', 'price_unit': 'day'},
            format='json',
        )
        self.assertEqual(first_a.status_code, status.HTTP_201_CREATED)

        duplicate_a = self.client.post(
            '/hiring/deals/',
            {'job_post': self.job_post.id, 'price': '1700.00', 'price_unit': 'day'},
            format='json',
        )
        self.assertEqual(duplicate_a.status_code, status.HTTP_400_BAD_REQUEST)

        # Path B duplicate check
        self.client.force_authenticate(user=self.client_user)
        first_b = self.client.post(
            '/hiring/deals/',
            {'worker_service': self.worker_service.id, 'price': '1900.00', 'price_unit': 'day'},
            format='json',
        )
        self.assertEqual(first_b.status_code, status.HTTP_201_CREATED)

        duplicate_b = self.client.post(
            '/hiring/deals/',
            {'worker_service': self.worker_service.id, 'price': '2000.00', 'price_unit': 'day'},
            format='json',
        )
        self.assertEqual(duplicate_b.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rule_5_user_cannot_create_deal_with_self(self):
        """Rule #5: A user cannot create a Deal with themselves (client != worker.client_profile)."""
        # Bob posts his own JobPost as a client, then tries to apply to it as a worker
        bobs_job = JobPost.objects.create(
            client=self.worker_client_profile,
            title='Bob own job',
            job_description='Testing self deal',
            city='Lahore',
            area='Model Town',
            category='handyman',
            duration_unit='day',
            duration='1 day',
            start_date=date.today() + timedelta(days=1),
            status='open',
        )
        self.client.force_authenticate(user=self.worker_user)
        self_job_res = self.client.post(
            '/hiring/deals/',
            {'job_post': bobs_job.id, 'price': '1000.00', 'price_unit': 'day'},
            format='json',
        )
        self.assertEqual(self_job_res.status_code, status.HTTP_400_BAD_REQUEST)

        # Bob also tries to hire his own WorkerService as a client
        self_service_res = self.client.post(
            '/hiring/deals/',
            {'worker_service': self.worker_service.id, 'price': '1000.00', 'price_unit': 'day'},
            format='json',
        )
        self.assertEqual(self_service_res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rule_6_offers_locked_after_status_agreed(self):
        """Rule #6: After status=agreed, offers are no longer allowed; price is locked."""
        self.client.force_authenticate(user=self.worker_user)
        res = self.client.post(
            '/hiring/deals/',
            {'job_post': self.job_post.id, 'price': '1800.00', 'price_unit': 'day'},
            format='json',
        )
        deal_id = res.data['id']

        self.client.force_authenticate(user=self.client_user)
        self.client.post(f'/hiring/deals/{deal_id}/accept/')

        # Trying to send another offer after agreement must fail with 400
        late_offer_res = self.client.post(
            f'/hiring/deals/{deal_id}/offers/',
            {'price': '1200.00', 'price_unit': 'day'},
            format='json',
        )
        self.assertEqual(late_offer_res.status_code, status.HTTP_400_BAD_REQUEST)

        deal = Deal.objects.get(id=deal_id)
        self.assertEqual(deal.agreed_price, Decimal('1800.00'))

    def test_rule_7_only_client_completes_and_cancel_reopens_assigned_job(self):
        """Rule #7: Only the client can mark a deal completed. Cancelling an assigned job reopens the JobPost."""
        self.client.force_authenticate(user=self.worker_user)
        res = self.client.post(
            '/hiring/deals/',
            {'job_post': self.job_post.id, 'price': '1800.00', 'price_unit': 'day'},
            format='json',
        )
        deal_id = res.data['id']

        self.client.force_authenticate(user=self.client_user)
        self.client.post(f'/hiring/deals/{deal_id}/accept/')
        self.job_post.refresh_from_db()
        self.assertEqual(self.job_post.status, 'assigned')

        # Worker tries to complete the deal -> must fail with 400
        self.client.force_authenticate(user=self.worker_user)
        worker_complete_res = self.client.post(f'/hiring/deals/{deal_id}/complete/')
        self.assertEqual(worker_complete_res.status_code, status.HTTP_400_BAD_REQUEST)

        # Worker cancels the agreed deal -> succeeds and reopens the JobPost
        cancel_res = self.client.post(f'/hiring/deals/{deal_id}/cancel/')
        self.assertEqual(cancel_res.status_code, status.HTTP_200_OK)
        self.assertEqual(cancel_res.data['status'], 'cancelled')

        self.job_post.refresh_from_db()
        self.assertEqual(self.job_post.status, 'open')

    def test_rule_8_only_two_parties_can_view_or_act_on_deal(self):
        """Rule #8: Only the two parties of a Deal can view or act on it."""
        self.client.force_authenticate(user=self.worker_user)
        res = self.client.post(
            '/hiring/deals/',
            {'job_post': self.job_post.id, 'price': '1800.00', 'price_unit': 'day'},
            format='json',
        )
        deal_id = res.data['id']

        # Mallory (outsider) lists deals -> sees empty list
        self.client.force_authenticate(user=self.outsider_user)
        list_res = self.client.get('/hiring/deals/')
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.data), 0)

        # Mallory tries to view, send offer, accept, or cancel Deal -> all return 403 Forbidden
        self.assertEqual(
            self.client.get(f'/hiring/deals/{deal_id}/').status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.post(
                f'/hiring/deals/{deal_id}/offers/',
                {'price': '900.00', 'price_unit': 'day'},
                format='json',
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.post(f'/hiring/deals/{deal_id}/accept/').status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.post(f'/hiring/deals/{deal_id}/cancel/').status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_rule_9_units_and_my_deals_filtering(self):
        """Rule #9 & Filters: Verify JobPost duration_unit, WorkerService price_unit, and ?role / ?status filters."""
        # Bob is the worker in Deal 1 (on Alice's JobPost)
        self.client.force_authenticate(user=self.worker_user)
        deal_as_worker = self.client.post(
            '/hiring/deals/',
            {'job_post': self.job_post.id, 'price': '1800.00', 'price_unit': 'day'},
            format='json',
        ).data['id']

        # Bob is the client in Deal 2 (hiring Mallory's WorkerService)
        mallory_service = WorkerService.objects.create(
            worker=self.outsider_worker_bio,
            category='cleaning',
            job_description='Deep house cleaning',
            city='Lahore',
            area='DHA',
            rate=Decimal('500.00'),
            price_unit='hour',
            is_available=True,
        )
        deal_as_client = self.client.post(
            '/hiring/deals/',
            {'worker_service': mallory_service.id, 'price': '450.00', 'price_unit': 'hour'},
            format='json',
        ).data['id']

        # Bob filters his deals by role=worker and role=client
        as_worker_res = self.client.get('/hiring/deals/?role=worker')
        self.assertEqual([d['id'] for d in as_worker_res.data], [deal_as_worker])

        as_client_res = self.client.get('/hiring/deals/?role=client')
        self.assertEqual([d['id'] for d in as_client_res.data], [deal_as_client])

        # Decline Deal 2 and filter by status
        self.client.post(f'/hiring/deals/{deal_as_client}/decline/')
        declined_res = self.client.get('/hiring/deals/?status=declined')
        self.assertEqual([d['id'] for d in declined_res.data], [deal_as_client])
