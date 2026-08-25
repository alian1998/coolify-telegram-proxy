FROM alpine:3.20 AS build

RUN apk add --no-cache gcc musl-dev make git linux-headers binutils

WORKDIR /src
ARG THREEPROXY_VERSION=1.0.0
RUN git clone --depth 1 --branch "${THREEPROXY_VERSION}" https://github.com/3proxy/3proxy.git . \
    && make -f Makefile.Linux \
    && test -x bin/3proxy

FROM alpine:3.20

RUN apk add --no-cache libgcc \
    && adduser -D -H -s /sbin/nologin proxy

COPY --from=build /src/bin/3proxy /usr/local/bin/3proxy
COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

USER proxy
EXPOSE 8080 1080
ENTRYPOINT ["/entrypoint.sh"]
