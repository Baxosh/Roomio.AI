from vanna.capabilities.sql_runner import SqlRunner
from vanna.core.user import RequestContext, User, UserResolver

from logging_config import get_logger

logger = get_logger(__name__)


# Create a simple user resolver
class SimpleUserResolver(UserResolver):
    def __init__(self, sql_runner: SqlRunner):
        self.sql_runner = sql_runner
        logger.info("SimpleUserResolver initialized")

    async def resolve_user(self, request_context: RequestContext) -> User:
        grms_user_id = request_context.get_cookie("user_id")
        logger.debug(f"Attempting to resolve user with ID: {grms_user_id}")

        # Check if user_id cookie is provided
        if not grms_user_id:
            error_msg = "Authentication required: No user_id cookie found. Please log in to continue."
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Query the database to get user information
        query = """
        SELECT id, email, is_superuser, is_staff, is_active, tenant_id
        FROM users_users
        WHERE id = %s
        """

        try:
            # Use psycopg2 directly for parameterized queries
            psycopg2 = self.sql_runner.psycopg2  # pyright: ignore
            conn_params = self.sql_runner.connection_params  # pyright: ignore

            logger.debug("Connecting to database to resolve user")
            with psycopg2.connect(**conn_params) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (grms_user_id,))
                    result = cursor.fetchone()

                    if result:
                        user_id = str(result[0])  # uuid as string
                        email = result[1]
                        is_superuser = result[2]
                        is_staff = result[3]
                        is_active = result[4]
                        tenant_id = str(result[5])

                        # Check if user account is active
                        if not is_active:
                            error_msg = f"User account is inactive: {email}. Please contact your administrator."
                            logger.warning(f"Inactive user attempted access: {email}")
                            raise ValueError(error_msg)

                        groups = []
                        if is_superuser or is_staff:
                            groups.append("admin")
                        if is_active:
                            groups.append("user")

                        logger.info(f"User resolved successfully: {email}, groups: {groups}, tenant_id: {tenant_id}")

                        return User(
                            id=user_id,
                            email=email,
                            group_memberships=groups,
                            metadata={"tenant_id": tenant_id},
                        )
                    else:
                        # User not found in database - raise error and stop
                        error_msg = f"User not found in database with ID: {grms_user_id}. Please ensure you are logged in with a valid account."
                        logger.error(error_msg)
                        raise ValueError(error_msg)

        except ValueError as _:
            # Re-raise ValueError (user not found, inactive, or missing cookie)
            raise
        except Exception as e:
            # Database connection or query error
            error_msg = f"Database error while resolving user: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg)
