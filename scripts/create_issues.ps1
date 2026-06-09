$ErrorActionPreference = 'Stop'
$owner = 'ricardocovo'
$repo  = 'app-api'
$slug  = "$owner/$repo"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
function New-Issue {
    param(
        [Parameter(Mandatory)] [string] $Title,
        [Parameter(Mandatory)] [string] $Body,
        [string[]] $Labels
    )
    $tmp = New-TemporaryFile
    Set-Content -Path $tmp -Value $Body -Encoding UTF8
    $args = @('issue','create','--repo',$slug,'--title',$Title,'--body-file',$tmp)
    foreach ($l in $Labels) { $args += @('--label',$l) }
    $url = & gh @args
    Remove-Item $tmp -Force
    if (-not $url) { throw "Failed to create issue: $Title" }
    $num = ($url -split '/')[-1]
    $id  = & gh api "repos/$slug/issues/$num" --jq '.id'
    Write-Host "Created #$num  $Title"
    return [pscustomobject]@{ Number = [int]$num; Id = [int]$id; Url = $url }
}

function Link-SubIssue {
    param(
        [Parameter(Mandatory)] [int] $ParentNumber,
        [Parameter(Mandatory)] [int] $ChildId
    )
    & gh api --method POST "repos/$slug/issues/$ParentNumber/sub_issues" -F "sub_issue_id=$ChildId" | Out-Null
    Write-Host "  linked child id $ChildId -> parent #$ParentNumber"
}

# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------
$labels = @(
    @{ name='phase-2'; color='1D76DB'; desc='Phase 2 - Data Models (SQLAlchemy)' },
    @{ name='phase-3'; color='0E8A16'; desc='Phase 3 - Pydantic Schemas' },
    @{ name='phase-4'; color='5319E7'; desc='Phase 4 - CRUD Layer' },
    @{ name='phase-5'; color='B60205'; desc='Phase 5 - API Routers' },
    @{ name='phase-6'; color='FBCA04'; desc='Phase 6 - Validation & Docs' },
    @{ name='epic';    color='C5DEF5'; desc='Parent / tracking issue' }
)
foreach ($lb in $labels) {
    & gh label create $lb.name --repo $slug --color $lb.color --description $lb.desc --force | Out-Null
}
Write-Host "Labels ready."

# ===========================================================================
# Shared context appended to every issue body
# ===========================================================================
$ctx = @'

---
### Project context
- **Stack:** Python 3.12, FastAPI, async SQLAlchemy 2.0, Alembic, SQL Server via `mssql+aioodbc` (ODBC Driver 18).
- **Layout:** `app/` with `main.py`, `core/config.py`, `db/session.py`, `db/base.py`, `models/`, `schemas/`, `crud/`, `api/routes/`.
- **PKs:** Integer identity (auto-increment).
- **Excluded:** `User.accessToken` / `User.refreshToken` are intentionally dropped this iteration. No auth/OAuth.
- **ERD entities:** User (1-N Profile), Profile (1-N ProfileFollow, 1-N ProfileChannel), ProfileFollow (FK followerId->User, FK profileId->Profile), ProfileChannel (FK profileId->Profile).
'@

# ===========================================================================
# PHASE 2 - Data Models (SQLAlchemy)
# ===========================================================================
$p2 = New-Issue -Title 'Phase 2 - Data Models (SQLAlchemy)' -Labels @('phase-2','epic') -Body @"
## Goal
Implement the four SQLAlchemy 2.0 ORM models (User, Profile, ProfileFollow, ProfileChannel) with typed ``Mapped[]`` columns, integer identity PKs, foreign keys, bidirectional relationships, and timestamp handling. Wire Alembic and produce the initial migration that creates all four tables against SQL Server.

## Scope
- ``app/db/base.py`` exposes a single ``Base(DeclarativeBase)`` and imports every model so Alembic ``target_metadata`` sees all tables.
- All models use ``Mapped[...]`` / ``mapped_column(...)`` typing (SQLAlchemy 2.0 style).
- Integer identity PKs (``primary_key=True, autoincrement=True``).
- Timestamps: ``created_at`` via ``server_default=func.now()``; ``updated_at`` via ``server_default=func.now(), onupdate=func.now()`` where the ERD defines ``updatedAt``.
- Column names map camelCase ERD fields to snake_case Python attributes where appropriate (document the convention chosen and keep it consistent).
- Relationships defined on **both** sides with explicit ``back_populates``.
- FK ``ondelete`` behaviour defined explicitly (see sub-issues).

## Acceptance criteria
- [ ] ``alembic upgrade head`` creates 4 tables with correct columns, PKs, FKs and indexes against SQL Server.
- [ ] ``alembic downgrade base`` cleanly drops everything.
- [ ] Models import without circular-import errors.
- [ ] ``Base.metadata.tables`` contains all 4 tables.

## Sub-issues
Tracked below. Complete the four model sub-issues before the Alembic migration sub-issue.
$ctx
"@

$p2User = New-Issue -Title 'Phase 2.1 - User model' -Labels @('phase-2') -Body @"
## Goal
Create ``app/models/user.py`` defining the ``User`` ORM model.

## Columns
| Attribute | Column | Type | Constraints |
|-----------|--------|------|-------------|
| ``id`` | ``id`` | Integer identity | PK, autoincrement |
| ``google_id`` | ``google_id`` | String(255) | unique, nullable=False, indexed |
| ``email`` | ``email`` | String(320) | unique, nullable=False, indexed |
| ``name`` | ``name`` | String(255) | nullable=True |
| ``avatar_url`` | ``avatar_url`` | String(1024) | nullable=True |
| ``created_at`` | ``created_at`` | DateTime(timezone=True) | server_default=now(), nullable=False |
| ``updated_at`` | ``updated_at`` | DateTime(timezone=True) | server_default=now(), onupdate=now(), nullable=False |

> ``accessToken`` / ``refreshToken`` are intentionally **excluded** this iteration.

## Relationships
- ``profiles: Mapped[list["Profile"]]`` — ``relationship(back_populates="user", cascade="all, delete-orphan")``.
- ``following: Mapped[list["ProfileFollow"]]`` — follows authored by this user (``ProfileFollow.follower_id``), ``back_populates="follower"``.

## Acceptance criteria
- [ ] Model uses ``Mapped[]`` typing.
- [ ] Unique constraints on ``google_id`` and ``email``.
- [ ] Both relationships resolve without import errors.
$ctx
"@

$p2Profile = New-Issue -Title 'Phase 2.2 - Profile model' -Labels @('phase-2') -Body @"
## Goal
Create ``app/models/profile.py`` defining the ``Profile`` ORM model.

## Columns
| Attribute | Column | Type | Constraints |
|-----------|--------|------|-------------|
| ``id`` | ``id`` | Integer identity | PK, autoincrement |
| ``name`` | ``name`` | String(255) | nullable=False |
| ``user_id`` | ``user_id`` | Integer | FK -> ``user.id`` ON DELETE CASCADE, nullable=False, indexed |
| ``is_default`` | ``is_default`` | Boolean | nullable=False, server_default false |
| ``is_public`` | ``is_public`` | Boolean | nullable=False, server_default false |
| ``created_at`` | ``created_at`` | DateTime(tz) | server_default=now() |
| ``updated_at`` | ``updated_at`` | DateTime(tz) | server_default=now(), onupdate=now() |

## Relationships
- ``user: Mapped["User"]`` — ``back_populates="profiles"``.
- ``follows: Mapped[list["ProfileFollow"]]`` — ``back_populates="profile", cascade="all, delete-orphan"``.
- ``channels: Mapped[list["ProfileChannel"]]`` — ``back_populates="profile", cascade="all, delete-orphan"``.

## Acceptance criteria
- [ ] FK ``user_id`` -> ``user.id`` with ``ondelete="CASCADE"``.
- [ ] Boolean defaults render correctly in SQL Server (``server_default=text("0")``).
- [ ] All three relationships resolve.
$ctx
"@

$p2Follow = New-Issue -Title 'Phase 2.3 - ProfileFollow model' -Labels @('phase-2') -Body @"
## Goal
Create ``app/models/profile_follow.py`` defining the ``ProfileFollow`` join-style model (a user following a profile).

## Columns
| Attribute | Column | Type | Constraints |
|-----------|--------|------|-------------|
| ``id`` | ``id`` | Integer identity | PK, autoincrement |
| ``follower_id`` | ``follower_id`` | Integer | FK -> ``user.id`` ON DELETE CASCADE, nullable=False, indexed |
| ``profile_id`` | ``profile_id`` | Integer | FK -> ``profile.id`` ON DELETE CASCADE, nullable=False, indexed |
| ``created_at`` | ``created_at`` | DateTime(tz) | server_default=now() |

## Constraints
- Composite unique constraint ``UniqueConstraint("follower_id", "profile_id", name="uq_follow_follower_profile")`` to prevent duplicate follows.

## Relationships
- ``follower: Mapped["User"]`` — ``back_populates="following"`` (FK ``follower_id``).
- ``profile: Mapped["Profile"]`` — ``back_populates="follows"`` (FK ``profile_id``).

## Acceptance criteria
- [ ] Two FKs with explicit ``foreign_keys`` disambiguation if needed.
- [ ] Unique constraint present.
- [ ] Relationships resolve in both directions.
$ctx
"@

$p2Channel = New-Issue -Title 'Phase 2.4 - ProfileChannel model' -Labels @('phase-2') -Body @"
## Goal
Create ``app/models/profile_channel.py`` defining the ``ProfileChannel`` model (a YouTube channel attached to a profile).

## Columns
| Attribute | Column | Type | Constraints |
|-----------|--------|------|-------------|
| ``id`` | ``id`` | Integer identity | PK, autoincrement |
| ``profile_id`` | ``profile_id`` | Integer | FK -> ``profile.id`` ON DELETE CASCADE, nullable=False, indexed |
| ``youtube_channel_id`` | ``youtube_channel_id`` | String(255) | nullable=False, indexed |
| ``channel_title`` | ``channel_title`` | String(512) | nullable=True |
| ``thumbnail_url`` | ``thumbnail_url`` | String(1024) | nullable=True |

## Constraints
- Composite unique constraint ``UniqueConstraint("profile_id", "youtube_channel_id", name="uq_channel_profile_ytid")``.

## Relationships
- ``profile: Mapped["Profile"]`` — ``back_populates="channels"``.

## Acceptance criteria
- [ ] FK ``profile_id`` -> ``profile.id`` with ``ondelete="CASCADE"``.
- [ ] Unique constraint present.
- [ ] Relationship resolves.
$ctx
"@

$p2Alembic = New-Issue -Title 'Phase 2.5 - Alembic init + initial migration' -Labels @('phase-2') -Body @"
## Goal
Initialise Alembic for async SQLAlchemy and generate/apply the initial migration creating all four tables.

## Tasks
- ``alembic init -t async migrations`` (async template).
- Point ``env.py`` ``target_metadata`` at ``app.db.base.Base.metadata``; import models package so all tables register.
- Read the DB URL from ``app.core.config.settings`` (do not hardcode in ``alembic.ini``).
- ``alembic revision --autogenerate -m "initial schema"``.
- Review the generated migration: confirm 4 tables, FKs with correct ``ondelete``, unique constraints, indexes.
- ``alembic upgrade head`` against a live SQL Server instance.

## Acceptance criteria
- [ ] ``alembic upgrade head`` creates ``user``, ``profile``, ``profile_follow``, ``profile_channel``.
- [ ] FKs and unique constraints match the model definitions.
- [ ] ``alembic downgrade base`` removes all tables cleanly.
- [ ] Migration is reproducible from an empty database.
$ctx
"@

Link-SubIssue -ParentNumber $p2.Number -ChildId $p2User.Id
Link-SubIssue -ParentNumber $p2.Number -ChildId $p2Profile.Id
Link-SubIssue -ParentNumber $p2.Number -ChildId $p2Follow.Id
Link-SubIssue -ParentNumber $p2.Number -ChildId $p2Channel.Id
Link-SubIssue -ParentNumber $p2.Number -ChildId $p2Alembic.Id

# ===========================================================================
# PHASE 3 - Pydantic Schemas
# ===========================================================================
$p3 = New-Issue -Title 'Phase 3 - Pydantic Schemas' -Labels @('phase-3','epic') -Body @"
## Goal
Define Pydantic v2 schemas for every entity (``Base``, ``Create``, ``Update``, ``Read``) plus shared pagination params and a generic ``Page`` response wrapper.

## Conventions
- Pydantic v2; ``Read`` schemas use ``model_config = ConfigDict(from_attributes=True)``.
- ``Create`` = required fields for insert (no server-generated fields).
- ``Update`` = all fields ``Optional`` for partial updates (PATCH semantics).
- ``Read`` = full record including ``id`` and timestamps.
- Field aliasing: accept/emit camelCase via ``alias`` + ``populate_by_name=True`` if the API contract is camelCase; otherwise keep snake_case. Decide once and document.

## Acceptance criteria
- [ ] Schemas import cleanly with no circular imports.
- [ ] ``/docs`` renders request/response models for all entities.
- [ ] ``Read`` schemas serialize ORM instances via ``from_attributes``.

## Sub-issues
Per-entity schema modules + shared pagination utilities.
$ctx
"@

$p3User = New-Issue -Title 'Phase 3.1 - User schemas' -Labels @('phase-3') -Body @"
## Goal
``app/schemas/user.py`` with ``UserBase``, ``UserCreate``, ``UserUpdate``, ``UserRead``.

## Fields
- **UserBase:** ``google_id: str``, ``email: EmailStr``, ``name: str | None``, ``avatar_url: str | None``.
- **UserCreate:** inherits ``UserBase`` (all required except nullable ones).
- **UserUpdate:** all fields ``Optional`` (``email``, ``name``, ``avatar_url``, ``google_id``).
- **UserRead:** ``UserBase`` + ``id: int``, ``created_at: datetime``, ``updated_at: datetime``; ``from_attributes=True``.

## Acceptance criteria
- [ ] ``email`` validated as ``EmailStr``.
- [ ] No token fields present.
- [ ] ``UserRead`` round-trips from a ``User`` ORM object.
$ctx
"@

$p3Profile = New-Issue -Title 'Phase 3.2 - Profile schemas' -Labels @('phase-3') -Body @"
## Goal
``app/schemas/profile.py`` with ``ProfileBase``, ``ProfileCreate``, ``ProfileUpdate``, ``ProfileRead``.

## Fields
- **ProfileBase:** ``name: str``, ``is_default: bool = False``, ``is_public: bool = False``.
- **ProfileCreate:** ``ProfileBase`` + ``user_id: int``.
- **ProfileUpdate:** ``name``, ``is_default``, ``is_public`` all ``Optional``.
- **ProfileRead:** ``ProfileBase`` + ``id: int``, ``user_id: int``, ``created_at``, ``updated_at``; ``from_attributes=True``.

## Acceptance criteria
- [ ] ``user_id`` required on create, immutable on update (not in ``ProfileUpdate``).
- [ ] Booleans default to ``False``.
$ctx
"@

$p3Follow = New-Issue -Title 'Phase 3.3 - ProfileFollow schemas' -Labels @('phase-3') -Body @"
## Goal
``app/schemas/profile_follow.py`` with ``ProfileFollowBase``, ``ProfileFollowCreate``, ``ProfileFollowRead``.

## Fields
- **ProfileFollowBase:** ``follower_id: int``, ``profile_id: int``.
- **ProfileFollowCreate:** inherits base.
- **ProfileFollowRead:** base + ``id: int``, ``created_at: datetime``; ``from_attributes=True``.

> No ``Update`` schema — follows are create/delete only.

## Acceptance criteria
- [ ] No update schema exposed.
- [ ] ``Read`` includes ``created_at``.
$ctx
"@

$p3Channel = New-Issue -Title 'Phase 3.4 - ProfileChannel schemas' -Labels @('phase-3') -Body @"
## Goal
``app/schemas/profile_channel.py`` with ``ProfileChannelBase``, ``ProfileChannelCreate``, ``ProfileChannelUpdate``, ``ProfileChannelRead``.

## Fields
- **ProfileChannelBase:** ``youtube_channel_id: str``, ``channel_title: str | None``, ``thumbnail_url: str | None``.
- **ProfileChannelCreate:** ``ProfileChannelBase`` + ``profile_id: int``.
- **ProfileChannelUpdate:** ``channel_title``, ``thumbnail_url`` ``Optional`` (``youtube_channel_id`` and ``profile_id`` immutable).
- **ProfileChannelRead:** base + ``id: int``, ``profile_id: int``; ``from_attributes=True``.

## Acceptance criteria
- [ ] ``profile_id`` required on create, absent from update.
- [ ] ``Read`` round-trips from ORM object.
$ctx
"@

$p3Page = New-Issue -Title 'Phase 3.5 - Pagination params + Page wrapper' -Labels @('phase-3') -Body @"
## Goal
``app/schemas/common.py`` (or ``pagination.py``) with reusable pagination utilities.

## Deliverables
- ``PaginationParams`` dependency: ``limit: int = Query(50, ge=1, le=200)``, ``offset: int = Query(0, ge=0)``.
- Generic ``Page[T]`` response model:
  - ``items: list[T]``
  - ``total: int``
  - ``limit: int``
  - ``offset: int``
- Implemented with ``Generic[T]`` / ``TypeVar`` so it works for every entity's ``Read`` schema.

## Acceptance criteria
- [ ] ``limit`` and ``offset`` validated with sensible bounds.
- [ ] ``Page[UserRead]`` (etc.) renders correctly in ``/docs``.
- [ ] Reusable across all list endpoints.
$ctx
"@

Link-SubIssue -ParentNumber $p3.Number -ChildId $p3User.Id
Link-SubIssue -ParentNumber $p3.Number -ChildId $p3Profile.Id
Link-SubIssue -ParentNumber $p3.Number -ChildId $p3Follow.Id
Link-SubIssue -ParentNumber $p3.Number -ChildId $p3Channel.Id
Link-SubIssue -ParentNumber $p3.Number -ChildId $p3Page.Id

# ===========================================================================
# PHASE 4 - CRUD Layer
# ===========================================================================
$p4 = New-Issue -Title 'Phase 4 - CRUD Layer' -Labels @('phase-4','epic') -Body @"
## Goal
Build a generic async CRUD base class and per-entity CRUD modules that extend it with entity-specific filters. All DB access is async (``AsyncSession``).

## Acceptance criteria
- [ ] Generic base supports get, get_multi (pagination + filtering + total count), create, update, delete.
- [ ] Each entity module exposes a singleton instance (e.g. ``user_crud``).
- [ ] All methods are ``async`` and accept an ``AsyncSession``.
- [ ] Update supports partial (PATCH) semantics from the ``*Update`` schema.

## Sub-issues
Generic base first, then the four entity modules.
$ctx
"@

$p4Base = New-Issue -Title 'Phase 4.1 - Generic async CRUDBase' -Labels @('phase-4') -Body @"
## Goal
``app/crud/base.py`` — generic ``CRUDBase[ModelType, CreateSchema, UpdateSchema]``.

## Methods
- ``get(db, id) -> ModelType | None``
- ``get_multi(db, *, limit, offset, filters: dict | None) -> tuple[list[ModelType], int]`` — returns rows **and** total count for the ``Page`` wrapper.
- ``create(db, *, obj_in: CreateSchema) -> ModelType``
- ``update(db, *, db_obj: ModelType, obj_in: UpdateSchema | dict) -> ModelType`` — uses ``model_dump(exclude_unset=True)`` for partial updates.
- ``delete(db, *, id) -> ModelType | None``

## Notes
- Use SQLAlchemy 2.0 ``select()`` style; count via ``select(func.count()).select_from(...)`` or a windowed count.
- ``filters`` applied as equality ``WHERE`` clauses on mapped columns.
- ``await db.commit()`` + ``await db.refresh(obj)`` on writes.

## Acceptance criteria
- [ ] Fully typed with ``Generic`` / ``TypeVar``.
- [ ] ``get_multi`` returns ``(items, total)``.
- [ ] Partial update ignores unset fields.
$ctx
"@

$p4User = New-Issue -Title 'Phase 4.2 - User CRUD' -Labels @('phase-4') -Body @"
## Goal
``app/crud/user.py`` — ``CRUDUser(CRUDBase)`` instance ``user_crud``.

## Entity-specific methods
- ``get_by_email(db, email) -> User | None``
- ``get_by_google_id(db, google_id) -> User | None``
- ``get_multi`` filter support for ``email`` (partial/eq) as needed.

## Acceptance criteria
- [ ] Lookups by ``email`` and ``google_id`` work.
- [ ] Duplicate email/google_id surface as integrity errors (handled in router layer).
$ctx
"@

$p4Profile = New-Issue -Title 'Phase 4.3 - Profile CRUD' -Labels @('phase-4') -Body @"
## Goal
``app/crud/profile.py`` — ``CRUDProfile(CRUDBase)`` instance ``profile_crud``.

## Entity-specific methods
- ``get_multi`` supports filtering by ``user_id``, ``is_public``, ``is_default``.
- Optional ``get_default_for_user(db, user_id)``.

## Acceptance criteria
- [ ] Filtering by ``user_id`` returns only that user's profiles, paginated with total.
- [ ] Combinable filters (e.g. ``user_id`` + ``is_public``).
$ctx
"@

$p4Follow = New-Issue -Title 'Phase 4.4 - ProfileFollow CRUD' -Labels @('phase-4') -Body @"
## Goal
``app/crud/profile_follow.py`` — ``CRUDProfileFollow(CRUDBase)`` instance ``follow_crud``.

## Entity-specific methods
- ``get_multi`` supports filtering by ``follower_id`` and/or ``profile_id``.
- ``create`` should guard the composite unique constraint (let DB enforce; translate ``IntegrityError`` in router to 409).
- Optional ``delete_by_pair(db, follower_id, profile_id)``.

## Acceptance criteria
- [ ] List follows by follower or by profile.
- [ ] Duplicate follow rejected (409 surfaced upstream).
$ctx
"@

$p4Channel = New-Issue -Title 'Phase 4.5 - ProfileChannel CRUD' -Labels @('phase-4') -Body @"
## Goal
``app/crud/profile_channel.py`` — ``CRUDProfileChannel(CRUDBase)`` instance ``channel_crud``.

## Entity-specific methods
- ``get_multi`` supports filtering by ``profile_id``.
- Respect composite unique constraint (``profile_id`` + ``youtube_channel_id``).

## Acceptance criteria
- [ ] List channels by ``profile_id`` with pagination + total.
- [ ] Duplicate channel for a profile rejected (409 surfaced upstream).
$ctx
"@

Link-SubIssue -ParentNumber $p4.Number -ChildId $p4Base.Id
Link-SubIssue -ParentNumber $p4.Number -ChildId $p4User.Id
Link-SubIssue -ParentNumber $p4.Number -ChildId $p4Profile.Id
Link-SubIssue -ParentNumber $p4.Number -ChildId $p4Follow.Id
Link-SubIssue -ParentNumber $p4.Number -ChildId $p4Channel.Id

# ===========================================================================
# PHASE 5 - API Routers
# ===========================================================================
$p5 = New-Issue -Title 'Phase 5 - API Routers' -Labels @('phase-5','epic') -Body @"
## Goal
Expose full CRUD REST endpoints per entity under ``/api/v1``, wired to the CRUD layer with the ``get_db`` dependency, proper status codes, 404/409 handling, and pagination/filtering.

## Endpoint convention (per entity)
- ``GET    /api/v1/{plural}``        -> ``Page[Read]`` (paginated + filtered)
- ``GET    /api/v1/{plural}/{id}``   -> ``Read`` (404 if missing)
- ``POST   /api/v1/{plural}``        -> ``Read`` (201)
- ``PATCH  /api/v1/{plural}/{id}``   -> ``Read`` (partial update, 404 if missing)
- ``DELETE /api/v1/{plural}/{id}``   -> 204 (404 if missing)

(``ProfileFollow`` omits PATCH — create/delete only.)

## Acceptance criteria
- [ ] All routers registered in ``main.py`` under ``/api/v1``.
- [ ] FK violations and duplicate-unique return 409 with a clear message.
- [ ] Missing resources return 404.
- [ ] Full CRUD round-trip verified per entity via ``/docs``.

## Sub-issues
One per router + registration/error-handling.
$ctx
"@

$p5Users = New-Issue -Title 'Phase 5.1 - Users router' -Labels @('phase-5') -Body @"
## Goal
``app/api/routes/users.py`` — ``APIRouter(prefix="/users", tags=["users"])``.

## Endpoints
- ``GET /users`` — ``Page[UserRead]``; query params: ``limit``, ``offset``, optional ``email`` filter.
- ``GET /users/{id}`` — ``UserRead`` (404).
- ``POST /users`` — ``UserCreate`` -> ``UserRead`` (201); 409 on duplicate ``email``/``google_id``.
- ``PATCH /users/{id}`` — ``UserUpdate`` -> ``UserRead`` (404).
- ``DELETE /users/{id}`` — 204 (404). Cascade deletes profiles/follows.

## Acceptance criteria
- [ ] Uses ``user_crud`` + ``get_db``.
- [ ] Duplicate email/google_id -> 409.
- [ ] Deleting a user cascades (verify FK behaviour).
$ctx
"@

$p5Profiles = New-Issue -Title 'Phase 5.2 - Profiles router' -Labels @('phase-5') -Body @"
## Goal
``app/api/routes/profiles.py`` — ``APIRouter(prefix="/profiles", tags=["profiles"])``.

## Endpoints
- ``GET /profiles`` — ``Page[ProfileRead]``; filters: ``user_id``, ``is_public``, ``is_default``, plus ``limit``/``offset``.
- ``GET /profiles/{id}`` — ``ProfileRead`` (404).
- ``POST /profiles`` — ``ProfileCreate`` -> ``ProfileRead`` (201); 409/400 if ``user_id`` FK invalid.
- ``PATCH /profiles/{id}`` — ``ProfileUpdate`` -> ``ProfileRead`` (404).
- ``DELETE /profiles/{id}`` — 204 (404). Cascade deletes follows/channels.

## Acceptance criteria
- [ ] Filtering by ``user_id`` works.
- [ ] Invalid ``user_id`` FK surfaces a clean 4xx, not a 500.
$ctx
"@

$p5Follows = New-Issue -Title 'Phase 5.3 - Follows router' -Labels @('phase-5') -Body @"
## Goal
``app/api/routes/follows.py`` — ``APIRouter(prefix="/follows", tags=["follows"])``. Create/list/delete only.

## Endpoints
- ``GET /follows`` — ``Page[ProfileFollowRead]``; filters: ``follower_id``, ``profile_id``, ``limit``/``offset``.
- ``GET /follows/{id}`` — ``ProfileFollowRead`` (404).
- ``POST /follows`` — ``ProfileFollowCreate`` -> ``ProfileFollowRead`` (201); 409 on duplicate (follower_id+profile_id); 4xx on invalid FK.
- ``DELETE /follows/{id}`` — 204 (404).

## Acceptance criteria
- [ ] Duplicate follow -> 409.
- [ ] No PATCH endpoint exposed.
- [ ] Filter by follower or profile.
$ctx
"@

$p5Channels = New-Issue -Title 'Phase 5.4 - Channels router' -Labels @('phase-5') -Body @"
## Goal
``app/api/routes/channels.py`` — ``APIRouter(prefix="/channels", tags=["channels"])``.

## Endpoints
- ``GET /channels`` — ``Page[ProfileChannelRead]``; filters: ``profile_id``, ``limit``/``offset``.
- ``GET /channels/{id}`` — ``ProfileChannelRead`` (404).
- ``POST /channels`` — ``ProfileChannelCreate`` -> ``ProfileChannelRead`` (201); 409 on duplicate (profile_id+youtube_channel_id); 4xx on invalid FK.
- ``PATCH /channels/{id}`` — ``ProfileChannelUpdate`` -> ``ProfileChannelRead`` (404).
- ``DELETE /channels/{id}`` — 204 (404).

## Acceptance criteria
- [ ] Filter by ``profile_id``.
- [ ] Duplicate channel -> 409.
$ctx
"@

$p5Wire = New-Issue -Title 'Phase 5.5 - Router registration + error handling' -Labels @('phase-5') -Body @"
## Goal
Register all routers and centralise error handling.

## Tasks
- In ``app/main.py``, include each router under a shared ``/api/v1`` prefix (e.g. an aggregate ``api_router`` in ``app/api/__init__.py``).
- Add exception handlers:
  - ``IntegrityError`` (unique / FK) -> 409 with a clear JSON body.
  - Not-found helper -> 404.
- Ensure ``RequestValidationError`` returns FastAPI default 422.
- Confirm ``/health`` and ``/docs`` still work.

## Acceptance criteria
- [ ] All four routers reachable under ``/api/v1``.
- [ ] DB integrity errors return 409, not 500.
- [ ] ``/docs`` shows every endpoint grouped by tag.
$ctx
"@

Link-SubIssue -ParentNumber $p5.Number -ChildId $p5Users.Id
Link-SubIssue -ParentNumber $p5.Number -ChildId $p5Profiles.Id
Link-SubIssue -ParentNumber $p5.Number -ChildId $p5Follows.Id
Link-SubIssue -ParentNumber $p5.Number -ChildId $p5Channels.Id
Link-SubIssue -ParentNumber $p5.Number -ChildId $p5Wire.Id

# ===========================================================================
# PHASE 6 - Validation & Docs
# ===========================================================================
$p6 = New-Issue -Title 'Phase 6 - Validation & Docs' -Labels @('phase-6','epic') -Body @"
## Goal
End-to-end validation of all endpoints, FK/constraint behaviour, and complete project documentation.

## Acceptance criteria
- [ ] Every endpoint smoke-tested (happy path + key error paths).
- [ ] FK constraints and cascade/restrict behaviour verified.
- [ ] README enables a fresh developer to run the project from scratch.
- [ ] End-to-end flow (User -> Profile -> Channel/Follow) passes.

## Sub-issues
Smoke testing, README, and the end-to-end flow check.
$ctx
"@

$p6Smoke = New-Issue -Title 'Phase 6.1 - Endpoint smoke tests + constraint checks' -Labels @('phase-6') -Body @"
## Goal
Manually (or via a script / HTTP collection) exercise every endpoint and verify constraint behaviour.

## Checklist
- [ ] CRUD round-trip for each entity (create -> read -> list -> update -> delete).
- [ ] Pagination: ``limit``/``offset`` boundaries behave; ``total`` is accurate.
- [ ] Filtering: ``profiles?user_id=``, ``channels?profile_id=``, ``follows?follower_id=``/``profile_id=``.
- [ ] 404 on missing ids for GET/PATCH/DELETE.
- [ ] 409 on duplicate unique (email, google_id, follow pair, channel pair).
- [ ] FK enforcement: creating a child with a non-existent parent id returns a clean 4xx.
- [ ] Cascade on delete: deleting a User removes its Profiles/Follows; deleting a Profile removes its Follows/Channels.

## Deliverable
A reusable ``.http`` / ``requests`` script or curl collection committed under ``scripts/`` or ``docs/``.
$ctx
"@

$p6Readme = New-Issue -Title 'Phase 6.2 - README & run docs' -Labels @('phase-6') -Body @"
## Goal
Author a complete ``README.md`` so a new developer can run the API from scratch.

## Sections
- Overview & ERD summary (4 entities, relationships).
- Prerequisites: Python 3.12, ODBC Driver 18 for SQL Server, a SQL Server instance.
- Environment: ``.env`` keys (copy from ``.env.example``), connection string format (``mssql+aioodbc://...?driver=ODBC+Driver+18+for+SQL+Server``).
- Install: virtualenv + ``pip install -r requirements.txt`` (or ``pyproject``).
- Migrations: ``alembic upgrade head`` / ``downgrade``.
- Run: ``uvicorn app.main:app --reload``; link to ``/docs`` and ``/health``.
- API reference: endpoint table per entity.

## Acceptance criteria
- [ ] A new dev can go from clone to running API following only the README.
- [ ] Env and migration steps documented.
$ctx
"@

$p6E2E = New-Issue -Title 'Phase 6.3 - End-to-end flow validation' -Labels @('phase-6') -Body @"
## Goal
Validate the primary domain flow end-to-end against a running instance + live SQL Server.

## Flow
1. ``POST /api/v1/users`` -> capture ``user.id``.
2. ``POST /api/v1/profiles`` with that ``user_id`` -> capture ``profile.id``.
3. ``POST /api/v1/channels`` with that ``profile_id``.
4. ``POST /api/v1/follows`` with a (second) ``follower_id`` + ``profile_id``.
5. ``GET`` list endpoints with filters to confirm relationships resolve.
6. ``DELETE`` the User and confirm cascade removed Profiles, Channels, and Follows.

## Acceptance criteria
- [ ] All steps succeed with correct status codes.
- [ ] Cascade delete leaves no orphan rows.
- [ ] Documented as a repeatable script.
$ctx
"@

Link-SubIssue -ParentNumber $p6.Number -ChildId $p6Smoke.Id
Link-SubIssue -ParentNumber $p6.Number -ChildId $p6Readme.Id
Link-SubIssue -ParentNumber $p6.Number -ChildId $p6E2E.Id

# ===========================================================================
# Summary
# ===========================================================================
Write-Host ""
Write-Host "=== Created parent issues ==="
Write-Host ("Phase 2: #{0}  {1}" -f $p2.Number, $p2.Url)
Write-Host ("Phase 3: #{0}  {1}" -f $p3.Number, $p3.Url)
Write-Host ("Phase 4: #{0}  {1}" -f $p4.Number, $p4.Url)
Write-Host ("Phase 5: #{0}  {1}" -f $p5.Number, $p5.Url)
Write-Host ("Phase 6: #{0}  {1}" -f $p6.Number, $p6.Url)
