#!/usr/bin/env sh

if [ "${USE_SONAR_JAVA:-}" == true ]; then
  echo "ZULU_VERSION=zulu17.46.19-ca-jdk17.0.9"
else
  echo "no"
fi
