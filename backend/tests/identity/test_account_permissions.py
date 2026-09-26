import pytest

from app.modules.identity.domain.account_management_policy import AccountManagementPolicy
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.identity.domain.user_role import UserRole


def _actor(role: UserRole, acts_as_artist: bool = False) -> AuthenticatedUser:
    import uuid

    return AuthenticatedUser(
        id=uuid.uuid4(),
        email=f"{role.lower()}@studio.ie",
        full_name="Someone",
        role=role,
        acts_as_artist=acts_as_artist,
    )


@pytest.fixture
def policy() -> AccountManagementPolicy:
    return AccountManagementPolicy()


@pytest.mark.parametrize(
    "target", [UserRole.OWNER, UserRole.MANAGER, UserRole.RESIDENT, UserRole.GUEST]
)
def test_owner_can_create_any_role(policy: AccountManagementPolicy, target: UserRole) -> None:
    assert policy.can_create(_actor(UserRole.OWNER), target) is True


@pytest.mark.parametrize("target", [UserRole.RESIDENT, UserRole.GUEST])
def test_manager_can_create_artists(policy: AccountManagementPolicy, target: UserRole) -> None:
    assert policy.can_create(_actor(UserRole.MANAGER), target) is True


@pytest.mark.parametrize("target", [UserRole.OWNER, UserRole.MANAGER])
def test_manager_cannot_create_staff(policy: AccountManagementPolicy, target: UserRole) -> None:
    """RN 2.2: o gerente nao atribui nem promove perfis administrativos."""
    assert policy.can_create(_actor(UserRole.MANAGER), target) is False


@pytest.mark.parametrize("actor_role", [UserRole.RESIDENT, UserRole.GUEST])
def test_artists_cannot_create_accounts(
    policy: AccountManagementPolicy, actor_role: UserRole
) -> None:
    assert policy.can_create(_actor(actor_role, acts_as_artist=True), UserRole.RESIDENT) is False


@pytest.mark.parametrize("target", [UserRole.OWNER, UserRole.MANAGER])
def test_manager_cannot_change_status_of_staff(
    policy: AccountManagementPolicy, target: UserRole
) -> None:
    """RN 2.5: o gerente nao bloqueia proprietario nem outro gerente."""
    assert policy.can_change_status(_actor(UserRole.MANAGER), target) is False


@pytest.mark.parametrize("target", [UserRole.RESIDENT, UserRole.GUEST])
def test_manager_can_change_status_of_artists(
    policy: AccountManagementPolicy, target: UserRole
) -> None:
    assert policy.can_change_status(_actor(UserRole.MANAGER), target) is True


def test_owner_can_change_status_of_anyone(policy: AccountManagementPolicy) -> None:
    for target in UserRole:
        assert policy.can_change_status(_actor(UserRole.OWNER), target) is True


def test_only_staff_can_list_accounts(policy: AccountManagementPolicy) -> None:
    assert policy.can_list(_actor(UserRole.OWNER)) is True
    assert policy.can_list(_actor(UserRole.MANAGER)) is True
    assert policy.can_list(_actor(UserRole.RESIDENT)) is False
    assert policy.can_list(_actor(UserRole.GUEST)) is False


def test_owner_who_tattoos_keeps_administrative_powers(
    policy: AccountManagementPolicy,
) -> None:
    """RN 2: proprietario e gerente que tambem tatuam conservam a alcada."""
    owner_artist = _actor(UserRole.OWNER, acts_as_artist=True)

    assert policy.can_create(owner_artist, UserRole.MANAGER) is True
    assert policy.can_list(owner_artist) is True
