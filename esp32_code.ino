#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <time.h>

// WiFi credentials
const char* ssid = "Vivo T1 5G";
const char* password = "123456789";

// MQTT Broker IP and Port
const char* mqtt_server = "192.168.223.249";
const int mqtt_port = 8883;

// Certificate from Mosquitto broker (ca.crt)
const char* ca_cert = "-----BEGIN CERTIFICATE-----\n"
"MIIDFTCCAf2gAwIBAgIUcvJDMl1MzIoCmx9Xip4QWXxZFsgwDQYJKoZIhvcNAQEL\n"
"BQAwGjEYMBYGA1UEAwwPMTkyLjE2OC4yMjMuMjQ5MB4XDTI1MDQwODE4MDM1N1oX\n"
"DTI2MDQwODE4MDM1N1owGjEYMBYGA1UEAwwPMTkyLjE2OC4yMjMuMjQ5MIIBIjAN\n"
"BgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA6lS7XiJ27B8KbeOLvPB7lp8Tuv4C\n"
"DIW2PyjL6ja3xS8+T9v+/iaVVwDfdeifgIMT4nvJ33XUVGjiOfbhXB/tJjj855Lh\n"
"fo3s1wbZJtg94Z26tCVtjmKNpiTOG0qgEE3TR/dEhvJxoJILUAASHsnkMzjlPBtz\n"
"gPSvnEuxWzzasn8D6h11j1zJUICbUummng/+Eknqk4UARVhxipXe0Gu+YmBog/3b\n"
"hQYQyJww1zrm+C/7h+0YOACQlMhkhrpKmWdCW/UWjn4EXNcYxKhZTY4tFZsNi9uy\n"
"lqHOJUWK3oeW9kUt+AphnjvzEHnFCE7s3DVpPNgKEi+cwWO+blVLht+96wIDAQAB\n"
"o1MwUTAdBgNVHQ4EFgQUI3Y407FsRp7+ODylDDgSx8SC9QgwHwYDVR0jBBgwFoAU\n"
"I3Y407FsRp7+ODylDDgSx8SC9QgwDwYDVR0TAQH/BAUwAwEB/zANBgkqhkiG9w0B\n"
"AQsFAAOCAQEAGoKE5LErL7A8X3Flcygu01Sdc+hjTSkdyOltL9cVUbVxSjsTwHzk\n"
"yYfDx7V0i1nwKH0Ejy22Q0mAjPYo5T0VIFd5gl87n+O6V1d180b/P1CN4oAc6D38\n"
"1W2fWmGeVyrM7aG10WYs2dZ1ZvFajNiC4KXfV+6YmHGW5XWI3FXh1BYR2IOITt1P\n"
"7IkQE9LePp6FSjRFNOTYW9FAzPHElCZFVdohunWH7DzIUaV3c1NjQ7Ler6sKfB5k\n"
"mI9KIHT4RKBr+iyRuCDtBpd32tCvY/Gla+8nvKdsjf/5stmgBsrzjWeg6inFhijX\n"
"7lSUDT9qDuNIkpL6boNqr2JQL+xXH94Pxw==\n"
"-----END CERTIFICATE-----\n";

// LED pins
const int redLED = 26;
const int greenLED = 27;

// Secure client and MQTT client
WiFiClientSecure espClient;
PubSubClient client(espClient);

// === Setup WiFi ===
void setup_wifi() {
    Serial.print("Connecting to WiFi: ");
    Serial.println(ssid);
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.print(".");
    }
    Serial.println("\nConnected to WiFi!");
}

// === Sync NTP time for TLS validation ===
void sync_time() {
    configTime(0, 0, "pool.ntp.org", "time.nist.gov");
    Serial.print("Syncing time");
    while (time(nullptr) < 100000) {
        Serial.print(".");
        delay(1000);
    }
    Serial.println("\nTime synchronized.");
}

// === Handle incoming messages ===
void callback(char* topic, byte* payload, unsigned int length) {
    payload[length] = '\0';
    String message = String((char*)payload);

    Serial.print("Received message: ");
    Serial.println(message);

    if (message == "red") {
        digitalWrite(redLED, HIGH);
        digitalWrite(greenLED, LOW);
    } else if (message == "green") {
        digitalWrite(redLED, LOW);
        digitalWrite(greenLED, HIGH);
    }
}

// === Reconnect to MQTT if dropped ===
void reconnect() {
    while (!client.connected()) {
        Serial.print("Connecting to MQTT broker... ");
        if (client.connect("ESP32_TLS_Client")) {
            Serial.println("connected!");
            client.subscribe("traffic/light");
        } else {
            Serial.print("failed, rc=");
            Serial.print(client.state());
            Serial.println(". Trying again in 5 seconds...");
            delay(5000);
        }
    }
}

void setup() {
    Serial.begin(115200);

    pinMode(redLED, OUTPUT);
    pinMode(greenLED, OUTPUT);

    setup_wifi();
    sync_time();

    espClient.setCACert(ca_cert); // Set the CA cert for TLS

    client.setServer(mqtt_server, mqtt_port);
    client.setCallback(callback);
}

void loop() {
    if (!client.connected()) {
        reconnect();
    }
    client.loop();
}
