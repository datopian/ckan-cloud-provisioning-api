# ckan-cloud-provisioner

API for provisioning CKAN instances in the ckan-cloud platform.

**API**:
- `GET /instances`
  returns a list of all running instances, their parameters and status.
  ```yaml
  {
      "results": [
          {"id": "instance-id", "params": "instance-params", "active": true/false, "ckanPhase": "Running/..." }
          # ...
      ]
  }
  ```
- `POST /instance`
  Create/edit an instance. Expects JSON body of the form:
  ```yaml
  {
      "id": "instance-id",
      "kind": "instance-kind",
      "param1": "value1",
      "param2": "value2",
      # ...
  }
  ```
  `id` is the unique identification of this new instance.
  `kind` is a predefined instance configuration.
  All other params are extra configuration (see later for usage)
- `DELETE /instance/id`
  Deletes instances by id.

- `GET /instance/kinds`
  returns a list of all possible instance kinds currently available in the system.
  ```yaml
  {
      "kinds": [
          {"id": "kind-id", "title": "kind-title"}, 
          # ... 
      ]
  }
  ```

- `GET /users`
  returns a list of all users and their roles.
  ```yaml
  {
      "results": [
          {
              "key": "email1@domain1.com",
              "value": {
                  "level": 2
              }
          },
          {
              "key": "email2@domain2.com",
              "value": {
                "level": 1
              }
          }
      ]
  }
  ```
  `level` 1 is maintainer, `level` 2 is admin.
- `POST /user`
  Create/edit a user. Expects JSON body of the form:
  ```yaml
  {
      "id": "users-email",
      "level": 1 # or 2
  }
  ```
- `DELETE /user/email@address.com`
  Deletes users by email.


All API calls should have a `jwt` query parameter with an authorization token for the 'ckan-cloud-provisioner' service (see github.com/datahq/auth for details).

**ENV VARS**:
- `INSTANCE_MANAGER`: SSH connection string to the cloud management API
- `PRIVATE_SSH_KEY`: RSA key for passwordless login to the cloud management API server
- `PRIVATE_KEY`: Private key for auth. Use this [script](https://github.com/datahq/auth/blob/master/tools/generate_key_pair.sh) to generate a key pair.
- `PUBLIC_KEY`: Public key for auth
- `GITHUB_KEY`: Github client key
- `GITHUB_SECRET`: Github client secret
- `DATABASE_URL`: Connection string to a postgres DB
- `EXTERNAL_ADDRESS`: External address where this app will be hosted (e.g. `http://provision.ckan.io`)

**Configuration Resolution**:

Create/Edit instance configuration is creating by overlaying a few configurations one on top of another.

- The base configuration is always `templates/aws-values.yaml`
- On top of that, a configuration is selected based on the instance `kind` parameter, found in `templates/kind-{kind}.yaml`
- Then, a configuration which is generated using `templates/templated.yaml`.
  This file is a configuration template, which uses values from the provided request body to render a values yaml file.
  Sample contents for `templated.yaml`:
  ```yaml
  domain: cloud-{{id}}.ckan.io
  registerSubdomain: "cloud-{{id}}"
  siteUrl: "http://{{externalAddress or 'cloud-'+id+'.ckan.io'}}"
  ```
- Finally, anything coming from the provided request body sans the `id` and `kind` parameters.

**DOCKER**:
```bash
$ docker build -t ckan-cloud-provisioner:latest .
$ docker run -p 8000:8000 \
   -e INSTANCE_MANAGER=$INSTANCE_MANAGER  \
   -e PRIVATE_SSH_KEY="$PRIVATE_SSH_KEY" \
   -e PRIVATE_KEY="$PRIVATE_KEY" \
   -e PUBLIC_KEY="$PUBLIC_KEY" \
   -e GITHUB_KEY=$GITHUB_KEY \
   -e GITHUB_SECRET=$GITHUB_SECRET \
   -e DATABASE_URL=$DATABASE_URL \
   -e EXTERNAL_ADDRESS=http://localhost:8000 \
   ckan-cloud-provisioner:latest
```