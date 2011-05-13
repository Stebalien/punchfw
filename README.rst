Description
===========
Punchfw monitors an application and opens ports when the application attempts to bind to them.

Setup
=====
1. Put punchfw_helper.py in a secure (root writable only) location and give it 0700 permissions.
2. Edit your sudoers and allow yourself to execute punchfw_helper.py without entering your password.

    <user_name>    ALL=NOPASSWD:/path/to/punchfw_helper.py

3. Set the HELPER_PATH variable in punchfw.py to the location of punchfw_helper.py.
4. Move punchfw.cfg to /etc/punchfw.cfg

Usage
=====
1. Add programs to the configuration file (/etc/punchfw.cfg)
    -> see the configuration file for details
2. Start these programs with punchfw.py <program-name>
