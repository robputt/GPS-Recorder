#include <SPI.h>
#include "SdFat.h"
#include <TinyGPS++.h>
#include <SoftwareSerial.h>

// Requires TinyGPS++ - https://github.com/mikalhart/TinyGPSPlus
// Requires SdFat - https://github.com/greiman/SdFat

static const int RXPin = 4, TXPin = 3;
static const uint32_t GPSBaud = 9600;

// TinyGPS++
TinyGPSPlus gps;
SoftwareSerial ss(RXPin, TXPin);

// SD Card
SdFat SD;
#define SD_CS_PIN 10
uint32_t nextWriteTime = 0;
int downloadMode = 0;

void setup()
{
  Serial.begin(9600);
  ss.begin(GPSBaud);

  Serial.println(F("Starting GPS Recorder"));
  Serial.println(F("Version 0.1"));
  Serial.print(F("GPS Version: "));
  Serial.println(TinyGPSPlus::libraryVersion());

  Serial.println();
  Serial.println("Waiting 30 seconds for computer connection to enter download mode...");
  while (millis() < 5000) {
    if (Serial.read() == 49) {
      downloadMode = 1;
    }
  }
  if (downloadMode) {
    Serial.println("Download mode requested, entering download mode.");
  } else {
    Serial.println("Download mode not requested, entering recorder mode.");
  }
  Serial.println();

  Serial.println("Initializing SD Card...");
  if (!SD.begin(SD_CS_PIN)) {
    Serial.println("SD card failed, or not present.");
    // don't do anything more:
    return;
  }
  Serial.println("SD Card Initialized.");
  Serial.println();

  if (downloadMode) {
    Serial.println("OK");
  }
}

void loop()
{
  if (downloadMode) {
    runDownloadMode();
  } else {
    runRecorderMode();
  }
}

void runDownloadMode() {
  String cmd = Serial.readString();
  cmd.trim();
  if (cmd == "ls") {
    File dir = SD.open("/");
    printDirectory(dir, true, false);
    Serial.println();
    Serial.println("OK");
  }
  if (cmd == "read") {
    Serial.println("READ");
    String fn = Serial.readString();
    fn.trim();
    File readfile = SD.open(fn);
    if (readfile) {
      while (readfile.available()) {
        Serial.write(readfile.read());
      }
    } else {
      Serial.println("ERR");
    }
    readfile.close();
    Serial.println("OK");
  }
  if (cmd == "wipe") {
    File dir = SD.open("/");
    printDirectory(dir, false, true);
    Serial.println("OK");
  }
}

void printDirectory(File dir, bool prt, bool rem) {
  if (prt) {
    Serial.print("[");
  }
  while (true) {
    File entry =  dir.openNextFile();
    if (! entry) {
      // no more files
      if (prt) {
        Serial.print("]");
      }
      break;
    }
    if (prt) {
      Serial.print("\"");
    }
    char cname[30];
    entry.getName(cname, 30);
    String fname;
    charToString(cname, fname);
    if (prt) {
      Serial.print(fname);
      Serial.print("\",");
    }
    entry.close();
    if (rem) {
      if(!SD.remove(cname)) {
        SD.rmdir(cname);
      }
    }
  }
}

void runRecorderMode() {
  // This sketch displays information every time a new sentence is correctly encoded.
  while (ss.available() > 0)
    if (gps.encode(ss.read())) {
      if(nextWriteTime <= millis()) {
        nextWriteTime = millis() + 2000;
        writeInfo();
      }
    }
  if (millis() > 5000 && gps.charsProcessed() < 10)
  {
    Serial.println(F("No GPS Detected"));
    while(true);
  }
}

void writeInfo()
{
    String line = "";
    if (gps.date.isValid())
    {
      line += gps.date.month();
      line += "/";
      line += gps.date.day();
      line += "/";
      line += gps.date.year();
    }
    else
    {
      line += "null";
    }
  
    if (gps.time.isValid())
    {
      line += " ";
      line += gps.time.hour();
      line += ":";
      line += gps.time.minute();
      line += ":";
      line += gps.time.second();
    }
    
    line += ", ";
    if (gps.location.isValid())
    {
      line += String(gps.location.lat(), 6);
      line += ", ";
      line += String(gps.location.lng(), 6);
      line += ", ";
      line += gps.altitude.meters();
    }
    else
    {
      line += "null, null, null";
    }
    Serial.println(line);
    File dataFile = SD.open("1", FILE_WRITE);
    if (dataFile) {
      dataFile.println(line);
    } else {
      Serial.println("Error writing to SD card");
    }
    dataFile.close();
}

void charToString(char S[], String &D)
{
 String rc(S);
 D = rc;
}
