import logging
import os
import sys
from dotenv import load_dotenv
from urllib.parse import quote_plus

from sshtunnel import SSHTunnelForwarder
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.exc import SQLAlchemyError

from .logger_config import setup_logger

load_dotenv()
logger = logging.getLogger(__name__)

def create_ssh_tunnel(
    ssh_host: str,
    ssh_username: str,
    ssh_private_key: str,
    remote_host: str,
    remote_port: int = 5432,
    local_port: int = 5432
) -> SSHTunnelForwarder:
    """
    Create an SSH tunnel to the database server

    Args:
        ssh_private_key: Either a path to the key file or the key content itself
    """
    try:
        if os.path.exists(ssh_private_key):
            ssh_key  = ssh_private_key

        else:
            # Assume it's the key content, write it to a temporary file
            import tempfile
            key_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
            key_file.write(ssh_private_key)
            key_file.close()
            ssh_key = key_file.name
            
        tunnel = SSHTunnelForwarder(
            (ssh_host, 22),
            ssh_username=ssh_username,
            ssh_pkey=ssh_key,
            remote_bind_address=(remote_host, remote_port),
            local_bind_address=("localhost", local_port)
        )

        tunnel.start()
        logger.info(f"SSH tunnel established to {ssh_username}@{ssh_host}")
        return tunnel

    except Exception as e:
        logger.error(f"Failed to establish SSH tunnel: {str(e)}")
        raise

def establish_db_connection(
        host: str,
        database: str, 
        user: str,
        password: str,
        port: str = "5432",
        use_ssh: bool = False,
        ssh_host: str = None,
        ssh_username: str = None,
        ssh_private_key: str = None,
        remote_host: str = None
) -> tuple[Engine, SSHTunnelForwarder | None]:
    """
    Establish connection to a postgresql database using sqlalchemy,
    optionally through SSH tunnel
    """
    try: 
        tunnel = None 
        if use_ssh:
            if not all([ssh_host, ssh_username, ssh_private_key, remote_host]):
                raise ValueError("SSH Parameters missing")
            tunnel = create_ssh_tunnel(
                ssh_host=ssh_host,
                ssh_username=ssh_username,
                ssh_private_key=ssh_private_key,
                remote_host=remote_host                
            )

            # Use tunnel's local binding
            host = "localhost"
            port = str(tunnel.local_bind_port)

        escaped_user = quote_plus(user)
        escaped_password = quote_plus(password)

        connection_string = f"postgresql://{escaped_user}:{escaped_password}@{host}:{port}/{database}"

        engine = create_engine(
            connection_string,
            pool_pre_ping=True, # Verify connection before using
            pool_size=5,        # Set pool size
            pool_recycle=3600,  # Recycle connections hourly
            max_overflow=10     # Allow extra connections
        )

        with engine.connect() as conn:
            conn.execute(text("select 1"))
            logger.info(f"Data base connection established to {user}@{host}:{port}/{database}")

        return engine, tunnel
    
    except SQLAlchemyError as e:
        if tunnel:
            tunnel.close()
        logger.error(f"Failed to establish connection to {user}@{host}:{port}/{database}")
        raise

if __name__ == "__main__":
    try:
        setup_logger()

        engine, tunnel = establish_db_connection(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            use_ssh=True,
            ssh_host=os.getenv('BASTION_HOST'),
            ssh_username=os.getenv('BASTION_USER'),
            ssh_private_key=os.getenv('SSH_PRIVATE_KEY'),
            remote_host=os.getenv('DB_HOST')
        )

        # Test the connection with a simple query
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();")).fetchone()
            logger.info(f"Connected to Postgres version: {result[0]}")

    except Exception as e:
        logger.error(f"Something went wrong in the db function: {str(e)}")
        sys.exit(1)

    finally:
        if engine:
            engine.dispose()
        if tunnel: 
            tunnel.close()
    