# QuickHire Backend Context

## 1. Stack & Settings (`config/`)
- **Stack**: Django 6.1, DRF 3.18, `django-filter`, SQLite (`db.sqlite3`).
- **Config (`config/`)**: `settings.py`, `urls.py`, `wsgi.py`, `asgi.py`.
- **Installed Apps**: `Client`, `worker`, `hiring`, `rest_framework`, `rest_framework.authtoken`, `rest_framework_simplejwt`, `rest_framework_simplejwt.token_blacklist`, `corsheaders` (`CorsMiddleware` enabled), `django_filters`.
- **DRF Settings**: Auth (`JWTAuthentication`, `TokenAuthentication`, `SessionAuthentication`), Permission (`IsAuthenticated`). Pagination/filters set per view.
- **JWT & CORS Settings**: `ACCESS_TOKEN_LIFETIME=30m`, `REFRESH_TOKEN_LIFETIME=7d`, `ROTATE_REFRESH_TOKENS=True`, `BLACKLIST_AFTER_ROTATION=True`. `CORS_ALLOWED_ORIGINS=['http://localhost:5173', 'http://127.0.0.1:5173']`.

## 2. Apps & Files
- **`Client/`**:
  - `models.py`: `ClientProfile`, `JobPost`, choice constants (`CATEGORY_CHOICES`, `JOB_STATUS_CHOICES`, `PRICE_UNIT_CHOICES`).
  - `serializer.py`: `ClientProfileSerializer`, `PostjobSerializer`, `MeSerializer`.
  - `views.py`: `ClientRegistrationView`, `PostjobView`, `MeView`, `LoginView`, `LogoutView`.
  - `ClientFilters.py`: `JobPostFilters` filterset.
  - `permissions.py`: `IsJobOwnerOrReadOnly`.
  - `pagination.py`: `JobPagination` (`page_size=10`).
  - `urls.py`: `/Client/` routes.
  - `admin.py`: Registers `ClientProfile`, `JobPost`.
  - `tests.py`: Empty.
- **`worker/`**:
  - `models.py`: `WorkerBio`, `WorkerService`.
  - `workerSerializer.py`: `WorkerBioOwnerSerializer`, `WorkerBioPublicSerializer`, `WorkerServiceSerializer`.
  - `views.py`: `WorkerBioView`, `WorkerServiceView`, `PublicWorkerListingView`.
  - `filters.py`: `WorkerServiceFilter` filterset.
  - `workerPermissions.py`: `IsWorkerBioOrReadOnly`, `IsWorkerServiceOrReadOnly`.
  - `urls.py`: `/worker/` routes.
  - `admin.py`: Registers `WorkerBio`, `WorkerService`.
  - `tests.py`: Empty.
- **`hiring/`**:
  - `models.py`: `Deal`, `Offer`, choice constants (`PARTY_CHOICES`, `DEAL_STATUS_CHOICES`, `ACTIVE_DEAL_STATUSES`, `OFFER_STATUS_CHOICES`), DB constraints.
  - `services.py`: `get_actor_role`, `create_deal`, `send_offer`, `accept_offer`, `decline_deal`, `cancel_deal`, `complete_deal`.
  - `serializers.py`: `OfferSerializer`, `OfferCreateSerializer`, `DealCreateSerializer`, `DealSerializer`.
  - `permissions.py`: `IsDealParty`.
  - `filters.py`: `DealFilter` (`role`, `status`, `job_post`, `worker_service`, `initiated_by`).
  - `views.py`: `DealViewSet` (thin ViewSet delegating to `services.py`).
  - `urls.py`: `/hiring/` routes.
  - `admin.py`: Registers `Deal`, `Offer`.
  - `tests.py`: `HiringWorkflowTests` (11 tests covering Path A, Path B, and Rules 1–9).

## 3. Models
`CATEGORY_CHOICES`: `driving`, `moving`, `handyman`, `caregiving`, `event_staffing`, `cooking`, `construction`, `security`, `gardening`, `tutoring`, `beauty`, `cleaning`.
`PRICE_UNIT_CHOICES`: `hour`, `day`, `week`, `month`, `flat`.

- **`Client.ClientProfile`**: `id`, `user` (OneToOne `auth.User`, `related_name='client_profile'`), `phone_number` (Char(15), null/blank), `profile_picture` (Image, null/blank), `average_rating` (Decimal(3,2), default=0), `created_at`, `updated_at`.
- **`Client.JobPost`** (ordering `['-created_at']`): `id`, `client` (FK `ClientProfile`, `related_name='job_posts'`), `title` (Char(150)), `job_description` (Text), `city` (Char(100)), `area` (Char(100)), `category` (Char(50), `CATEGORY_CHOICES`), `duration_unit` (Char(10), `PRICE_UNIT_CHOICES`), `duration` (Char(100)), `start_date` (Date), `status` (Char(20): `open`, `assigned`, `completed`, `cancelled`, default=`open`), `created_at`, `updated_at`. *(No price on JobPost; workers propose price during negotiation.)*
- **`worker.WorkerBio`**: `id`, `client_profile` (OneToOne `ClientProfile`, `related_name='worker_bio'`), `cnic` (Char(15), `unique=True`), `age` (PositiveInt, 18–100), `years_of_experience` (PositiveInt, default=0), `expertise_categories` (Char(50), `CATEGORY_CHOICES`, null/blank), `gender` (Char(1): `M`, `F`, `O`, blank), `bio` (Text, blank), `is_verified` (Bool, default=False), `average_rating` (Decimal(3,2), default=0), `created_at`, `updated_at`.
- **`worker.WorkerService`** (ordering `['-created_at']`): `id`, `worker` (FK `WorkerBio`, `related_name='services'`), `category` (Char(50), `CATEGORY_CHOICES`), `job_description` (Text), `city` (Char(100)), `area` (Char(100)), `rate` (Decimal(10,2)), `price_unit` (Char(10), `PRICE_UNIT_CHOICES`), `is_available` (Bool, default=True), `created_at`, `updated_at`.
- **`hiring.Deal`** (ordering `['-created_at']`): `id`, `client` (FK `ClientProfile`, `related_name='deals_as_client'`), `worker` (FK `WorkerBio`, `related_name='deals_as_worker'`), `job_post` (FK `JobPost`, null/blank, `related_name='deals'`), `worker_service` (FK `WorkerService`, null/blank, `related_name='deals'`), `initiated_by` (Char(10): `client`, `worker`), `status` (Char(20): `negotiating`, `agreed`, `in_progress`, `completed`, `declined`, `cancelled`, `expired`, default=`negotiating`), `agreed_price` (Decimal(10,2), null/blank), `price_unit` (Char(10), `PRICE_UNIT_CHOICES`, null/blank), `agreed_at` (DateTime, null/blank), `completed_at` (DateTime, null/blank), `created_at`, `updated_at`.
  - **Constraints**:
    - `deal_must_have_exactly_one_source`: XOR `CheckConstraint` on `(job_post, worker_service)`.
    - `unique_active_deal_per_job_and_worker`: Partial `UniqueConstraint` on `(job_post, worker)` where `status` in `['negotiating', 'agreed', 'in_progress']`.
    - `unique_active_deal_per_service_and_client`: Partial `UniqueConstraint` on `(worker_service, client)` where `status` in `['negotiating', 'agreed', 'in_progress']`.
- **`hiring.Offer`** (ordering `['created_at', 'id']`): `id`, `deal` (FK `Deal`, `related_name='offers'`), `sender` (Char(10): `client`, `worker`), `price` (Decimal(10,2), `> 0`), `price_unit` (Char(10), `PRICE_UNIT_CHOICES`), `message` (Text, blank), `status` (Char(20): `pending`, `accepted`, `superseded`, `declined`, default=`pending`), `created_at`.
  - **Constraints**:
    - `unique_pending_offer_per_deal`: Partial `UniqueConstraint` on `(deal,)` where `status='pending'`.
    - `offer_price_must_be_positive`: `CheckConstraint` (`price > 0`).

## 4. URLs
- `POST /Client/registration/` -> `ClientRegistrationView` -> `ClientProfileSerializer` -> `AllowAny`.
- `POST /api-token-auth/`, `POST /Client/login/` -> `LoginView` -> `AuthTokenSerializer` -> `AllowAny`.
- `POST /Client/token/refresh/` -> `TokenRefreshView` -> `TokenRefreshSerializer` -> `AllowAny`.
- `POST /Client/logout/` -> `LogoutView` -> blacklists refresh token (`205 Reset Content`) -> `IsAuthenticated`.
- `GET, PUT, PATCH /Client/me/` -> `MeView` -> `MeSerializer` -> `IsAuthenticated`.
- `GET, POST /Client/jobs/`, `GET, PUT, PATCH, DELETE /Client/jobs/<id>/` -> `PostjobView` -> `PostjobSerializer` -> `IsAuthenticated`, `IsJobOwnerOrReadOnly`.
- `GET, POST /worker/workerBio/`, `GET, PUT, PATCH, DELETE /worker/workerBio/<id>/` -> `WorkerBioView` -> `WorkerBioOwnerSerializer` (write) / `WorkerBioPublicSerializer` (read) -> `IsAuthenticated`, `IsWorkerBioOrReadOnly`.
- `GET, POST /worker/workerService/`, `GET, PUT, PATCH, DELETE /worker/workerService/<id>/` -> `WorkerServiceView` -> `WorkerServiceSerializer` -> `IsAuthenticated`, `IsWorkerServiceOrReadOnly`.
- `GET /worker/browseworkers/` -> `PublicWorkerListingView` -> `WorkerServiceSerializer` -> `AllowAny`.
- `GET, POST /hiring/deals/` -> `DealViewSet` (`list`, `create`) -> `DealSerializer` (read) / `DealCreateSerializer` (write) -> `IsAuthenticated`, `IsDealParty`.
- `GET /hiring/deals/<id>/` -> `DealViewSet` (`retrieve`) -> `DealSerializer` -> `IsAuthenticated`, `IsDealParty`.
- `POST /hiring/deals/<id>/offers/` -> `DealViewSet.offers` -> `OfferCreateSerializer` (in) / `OfferSerializer` (out) -> `IsAuthenticated`, `IsDealParty`.
- `POST /hiring/deals/<id>/accept/` -> `DealViewSet.accept` -> `DealSerializer` -> `IsAuthenticated`, `IsDealParty`.
- `POST /hiring/deals/<id>/decline/` -> `DealViewSet.decline` -> `DealSerializer` -> `IsAuthenticated`, `IsDealParty`.
- `POST /hiring/deals/<id>/cancel/` -> `DealViewSet.cancel` -> `DealSerializer` -> `IsAuthenticated`, `IsDealParty`.
- `POST /hiring/deals/<id>/complete/` -> `DealViewSet.complete` -> `DealSerializer` -> `IsAuthenticated`, `IsDealParty`.

## 5. Filters, Search, Ordering & Pagination
- **`/Client/jobs/`**: `JobPostFilters` (`city` iexact, `area` iexact, `category`, `status`) + `?mine=true`; Ordering: `created_at`, `start_date`; Pagination: `JobPagination` (10/page).
- **`/worker/browseworkers/`**: `WorkerServiceFilter` (`min_rate`, `max_rate`, `city` iexact, `area` iexact, `category`, `is_available`); Search: `job_description`, `worker__client_profile__user__first_name`, `worker__client_profile__user__last_name`; Ordering/Pagination: None.
- **`/hiring/deals/`**: `DealFilter` (`?role=client|worker`, `?status=...`, `?job_post=...`, `?worker_service=...`, `?initiated_by=client|worker`).
- **`/worker/workerBio/`, `/worker/workerService/`**: None.

## 6. Auth Flow
Register via `POST /Client/registration/` (`User` + `ClientProfile`); workers then `POST /worker/workerBio/`. Login (`POST /Client/login/` or `/api-token-auth/`) returns `{"access": "<jwt>", "refresh": "<jwt>", "token": "<str>", "client_profile_id": <int|None>, "worker_bio_id": <int|None>, "is_worker": <bool>}`. Refresh via `POST /Client/token/refresh/` (`{"refresh": "<jwt>"}` -> `{"access": "<jwt>", "refresh": "<jwt>"}`). Logout via `POST /Client/logout/` (`{"refresh": "<jwt>"}` -> `205 Reset Content`).

## 7. Sensitive Fields
- `cnic`: In `WorkerBioOwnerSerializer` (write); omitted in `WorkerBioPublicSerializer` (read) and `WorkerServiceSerializer`.
- `username`, `email`, `password`, `first_name`, `last_name`: `write_only` on `ClientProfileSerializer`.

## 8. Migrations
- **`Client`**: Applied through `0008_rename_price_unit_jobpost_duration_unit_and_more`; none pending.
- **`worker`**: Applied through `0005_workerservice_price_unit`; none pending.
- **`hiring`**: Applied through `0001_initial`; none pending.

## 9. Quirks & Design Notes
- Mixed casing: `Client/` vs `worker/` vs `hiring/`, `requirments.txt` typo.
- `WorkerBio` links OneToOne to `ClientProfile`, not `User`.
- `WorkerBio.expertise_categories` is plural but stores one `CharField`.
- `JobPost` has no `price` (uses `duration_unit` + `duration` so workers quote the price); `WorkerService` has `rate` + `price_unit`.
- All hiring business logic is enforced inside `hiring/services.py` (covered by 11 automated tests in `hiring/tests.py`).

## 10. NOT BUILT
- **NOT BUILT**: Reviews/rating calculation.
