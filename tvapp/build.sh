#!/usr/bin/env bash
# Builds the TV app without Gradle: aapt2 -> javac -> d8 -> zipalign -> apksigner.
set -euo pipefail
cd "$(dirname "$0")"
BT=$(ls -d "$ANDROID_HOME"/build-tools/* | sort -V | tail -1)
PLAT=$(ls -d "$ANDROID_HOME"/platforms/android-* | sort -V | tail -1)
echo "build-tools: $BT / platform: $PLAT"
rm -rf out && mkdir -p out/res out/classes out/dex
"$BT/aapt2" compile --dir res -o out/res
"$BT/aapt2" link -o out/base.apk -I "$PLAT/android.jar" --manifest AndroidManifest.xml \
  --min-sdk-version 21 --target-sdk-version 30 --version-code "${VERSION_CODE:-1}" --version-name "1.${VERSION_CODE:-1}" out/res/*.flat
javac -source 8 -target 8 -nowarn -classpath "$PLAT/android.jar" -d out/classes $(find src -name '*.java')
"$BT/d8" --lib "$PLAT/android.jar" --min-api 21 --output out/dex $(find out/classes -name '*.class')
(cd out/dex && zip -q ../base.apk classes.dex)
"$BT/zipalign" -f 4 out/base.apk out/aligned.apk
keytool -genkeypair -keystore out/ci.jks -storepass android -keypass android -alias hq -keyalg RSA -keysize 2048 \
  -validity 10000 -dname "CN=hakawati-tv" >/dev/null 2>&1
"$BT/apksigner" sign --ks out/ci.jks --ks-pass pass:android --key-pass pass:android --out out/hq.apk out/aligned.apk
"$BT/apksigner" verify out/hq.apk && ls -la out/hq.apk
