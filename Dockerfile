# --- Build stage: compile/install Python dependencies in throw-away layer ---
FROM python:3-alpine AS builder

# Build-only dependencies (kept out of the final image)
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev

COPY requirements.txt /tmp/requirements.txt
# --prefix isolates the installed packages so we can copy just them
RUN pip install --no-cache-dir --prefix=/install -r /tmp/requirements.txt

# --- Runtime stage ---
FROM python:3-alpine

# Only the installed packages are copied over: no compiler, no pip cache
COPY --from=builder /install /usr/local

WORKDIR /app
COPY knot.py /app/knot.py

# Run as a non-root user
RUN adduser -D -H -u 1000 knot && chown -R knot:knot /app
USER knot

ENV PORT=5000
EXPOSE 5000

CMD ["python", "knot.py"]
