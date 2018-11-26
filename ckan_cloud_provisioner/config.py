import os

# Where to connect to
instance_manager = os.environ.get('INSTANCE_MANAGER')

# Wait for results this long
default_timeout = 20

# Cancel a job after this long
default_cancel_timeout = 300