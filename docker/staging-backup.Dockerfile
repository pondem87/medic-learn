FROM postgres:17.6@sha256:00bc86618629af00d2937fdc5a5d63db3ff8450acf52f0636ec813c7f4902929
RUN apt-get update \
    && apt-get install -y --no-install-recommends awscli ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY docker/staging-backup.sh /usr/local/bin/staging-backup
RUN chmod 755 /usr/local/bin/staging-backup
ENTRYPOINT ["/usr/local/bin/staging-backup"]
