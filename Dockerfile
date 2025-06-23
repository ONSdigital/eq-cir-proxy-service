FROM python:3.12.6-alpine

WORKDIR /eq_cir_proxy_service

COPY pyproject.toml poetry.lock /eq_cir_proxy_service/

RUN pip install --no-cache-dir poetry==1.8.4 && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --with dev

COPY eq_cir_proxy_service eq_cir_proxy_service

ENV LOG_LEVEL=INFO

# Create a non-root user and group
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Change ownership of the application directory to the non-root user
RUN chown -R appuser:appgroup /eq_cir_proxy_service

# Set the user running the application to the non-root user
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5050/docs || exit 1

CMD ["uvicorn", "eq_cir_proxy_service.main:app", "--host", "0.0.0.0", "--port", "5050"]
