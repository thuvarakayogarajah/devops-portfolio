# Rationale for the Docker Optimizations

> **Note on AI tools:** I used an AI assistant (Claude) to phrase the explanations in this document, to draft the section on the multi-stage build and to double-check the percentage calculation. I implemented the Dockerfile optimizations and the `.dockerignore` and measured the image sizes myself. Afterwards, I checked the texts against my setup and adjusted them.

## Result
Naive image: 418 MB – optimized image: 236 MB.

The optimized image is **182 MB smaller**, a reduction of **about 43.5 %** (182 / 418 ≈ 0.435).

## Slim Base Image
`python:3.12` is based on a full Debian image and includes many packages the app doesn't need at runtime: compilers (gcc), header files, development libraries, tools such as git and curl, plus documentation and man pages. `python:3.12-slim` contains only what is needed to run Python.

This is beneficial for several reasons:
- **Smaller image:** faster pulls and pushes, less storage in the registry and on the hosts.
- **Smaller attack surface:** any installed package can contain vulnerabilities. Fewer packages mean fewer potential CVEs and fewer tools an attacker could use inside the container.
- **Explicit dependencies:** anything the app needs has to be installed deliberately.

## Multi-Stage Build
The Docker has two stages: the 'builder' stage installs the dependencies from requirements.txt into a separate folder('/install') and the runtime stage starts fresh from the slim base image and copies only the this folder 
with 'COPY --from-builder'. Everything else from the installation in the builder and is not part of the final image. 
For this app the size benefit is small, because both stages use slim and no compilers are needed. The multi-stage setup becomes more important as soon as a dependency needs tools such as gcc.

## Layer Order
Docker builds an image layer by layer and caches each layer. When a layer changes, that layer and every layer after it are rebuilt.

Dependencies change rarely, while the code changes often. That's why only `requirements.txt` is copied first and `pip install` runs next. The rest of the code is copied afterwards.

If **only the code** changes before the next build, `requirements.txt` stays the same. Docker reuses the cached layer with the installed dependencies and only reruns the `COPY` step for the code, so the build takes seconds instead of minutes. If the code were copied before the installation, every code change would trigger a full reinstall of all packages.

## .dockerignore
Excluded files include:
- `.git/` (version history, large and unnecessary in the container)
- `__pycache__/`, `*.pyc` (local bytecode files)
- `.venv/` or `venv/` (local virtual environment; the container builds its own)
- `.env` (local environment variables and secrets)


This keeps the build context small, speeds up the build and keeps unnecessary files out of the image.

This matters most for **`.env`**, because the file typically holds passwords, API keys or database credentials. If `COPY . .` copied it into the image, the secrets would be stored permanently in an image layer. Anyone who can pull the image, for example from a registry, could read them. Even if the file were deleted in a later layer, it would remain in the layer history. Secrets should be passed in at runtime instead, e.g. with `docker run --env-file` or through the orchestrator's secrets.

## Unprivileged User
By default, processes in a container run as `root`. If the application is compromised, for example through a vulnerability in a dependency, an attacker would have full privileges inside the container. They could modify files and install packages. If a container escape vulnerability exists, they would also have a much better chance of breaking out to the host.

Running as the dedicated user `appuser` follows the **principle of least privilege**: the app only has the permissions it actually needs, so a successful attack does less damage. Many platforms also require containers not to run as root, e.g. Kubernetes with suitable security policies, or OpenShift.

