#include <LiquidCrystal_I2C.h>
#include <Wire.h>

float VOLUME_FIXATION         = 0.60;
float VOLUME_PERMEABILIZATION = 0.60;
float VOLUME_ANTIBODY1        = 0.60;
float VOLUME_ANTIBODY2        = 0.60;
float VOLUME_WASH             = 0.80;
const float VOLUME_BONUS      = 0.20;

int WASH_CYCLES = 1;

unsigned long PAUSE_FIXATION         = 3000;
unsigned long PAUSE_PERMEABILIZATION = 3000;
unsigned long PAUSE_ANTIBODY1        = 3000;
unsigned long PAUSE_ANTIBODY2        = 3000;

const unsigned long DURATION_VACUUM = 15000;

const int BUTTON                = 8;
const int PUMP_FIXATION         = 2;
const int PUMP_WASH             = 4;
const int PUMP_PERMEABILIZATION = 3;
const int PUMP_ANTIBODY1        = 5;
const int PUMP_ANTIBODY2        = 6;
const int PUMP_VACUUM           = 7;

const float FR_FIXATION         = 0.927;
const float FR_WASH             = 1.040;
const float FR_PERMEABILIZATION = 0.787;
const float FR_ANTIBODY1        = 0.986;
const float FR_ANTIBODY2        = 1.044;
const float FR_VACUUM           = 31.20;

LiquidCrystal_I2C lcd(0x27, 20, 4);

bool sequenceRunning = false;

void setup() {
  Serial.begin(9600);
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Waiting for GUI...");

  pinMode(BUTTON,                INPUT_PULLUP);
  pinMode(PUMP_FIXATION,         OUTPUT); digitalWrite(PUMP_FIXATION,         LOW);
  pinMode(PUMP_WASH,             OUTPUT); digitalWrite(PUMP_WASH,             LOW);
  pinMode(PUMP_PERMEABILIZATION, OUTPUT); digitalWrite(PUMP_PERMEABILIZATION, LOW);
  pinMode(PUMP_ANTIBODY1,        OUTPUT); digitalWrite(PUMP_ANTIBODY1,        LOW);
  pinMode(PUMP_ANTIBODY2,        OUTPUT); digitalWrite(PUMP_ANTIBODY2,        LOW);
  pinMode(PUMP_VACUUM,           OUTPUT); digitalWrite(PUMP_VACUUM,           LOW);
}

void parseVolumes(String line) {
  line.replace("VOL:", "");
  int idx = 0;

  float vals[5];
  for (int i = 0; i < 5; i++) {
    int comma = line.indexOf(',', idx);
    String token = (comma == -1) ? line.substring(idx) : line.substring(idx, comma);
    vals[i] = token.toFloat();
    idx = comma + 1;
  }

  int comma = line.indexOf(',', idx);
  WASH_CYCLES = line.substring(idx, comma).toInt();
  if (WASH_CYCLES < 1) WASH_CYCLES = 1;
  idx = comma + 1;

  unsigned long pauses[4];
  for (int i = 0; i < 4; i++) {
    comma = line.indexOf(',', idx);
    String token = (comma == -1) ? line.substring(idx) : line.substring(idx, comma);
    pauses[i] = (unsigned long)(token.toFloat() * 1000.0);
    idx = comma + 1;
  }

  VOLUME_FIXATION         = vals[0];
  VOLUME_PERMEABILIZATION = vals[1];
  VOLUME_ANTIBODY1        = vals[2];
  VOLUME_ANTIBODY2        = vals[3];
  VOLUME_WASH             = vals[4];

  PAUSE_FIXATION         = pauses[0];
  PAUSE_PERMEABILIZATION = pauses[1];
  PAUSE_ANTIBODY1        = pauses[2];
  PAUSE_ANTIBODY2        = pauses[3];

  Serial.println("ACK:volumes_received");
  lcd.clear();
  lcd.print("Volumes set.");
  lcd.setCursor(0, 1);
  lcd.print("Wash x");
  lcd.print(WASH_CYCLES);
}

void pump(int pin, const char* label, float volume_mL, float flowRate_mL_min) {
  unsigned long duration = (unsigned long)((volume_mL / flowRate_mL_min) * 60000.0);

  Serial.print("STEP:");
  Serial.print(label);
  Serial.print(",");
  Serial.println(duration);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(label);
  lcd.setCursor(0, 1);
  lcd.print(volume_mL);
  lcd.print(" mL");

  digitalWrite(pin, HIGH);
  delay(duration);
  digitalWrite(pin, LOW);

  Serial.println("DONE");
}

void vacuum() {
  Serial.print("STEP:Vacuum,");
  Serial.println(DURATION_VACUUM);

  lcd.clear();
  lcd.print("Vacuum");
  digitalWrite(PUMP_VACUUM, HIGH);
  delay(DURATION_VACUUM);
  digitalWrite(PUMP_VACUUM, LOW);

  Serial.println("DONE");
}

void washCycle() {
  for (int i = 0; i < WASH_CYCLES; i++) {
    vacuum();
    pump(PUMP_WASH, "Wash",           VOLUME_WASH,                FR_WASH);
  }
  vacuum();
  pump(PUMP_WASH, "Cleaning tubes", VOLUME_WASH + VOLUME_BONUS, FR_WASH);
  vacuum();
}

void turnOffAllPumps() {
  digitalWrite(PUMP_FIXATION,         LOW);
  digitalWrite(PUMP_WASH,             LOW);
  digitalWrite(PUMP_PERMEABILIZATION, LOW);
  digitalWrite(PUMP_ANTIBODY1,        LOW);
  digitalWrite(PUMP_ANTIBODY2,        LOW);
  digitalWrite(PUMP_VACUUM,           LOW);
}

void incubate(const char* label, unsigned long duration_ms) {
  Serial.print("STEP:");
  Serial.print(label);
  Serial.print(",");
  Serial.println(duration_ms);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Incubating:");
  lcd.setCursor(0, 1);
  lcd.print(label);

  delay(duration_ms);
  Serial.println("DONE");
}

// ---------------------------------------------------------------
void runSequence() {
  sequenceRunning = true;
  Serial.println("SEQ:start");

  pump(PUMP_FIXATION,         "Fixation",   VOLUME_FIXATION,         FR_FIXATION);
  incubate("Fixation",         PAUSE_FIXATION);
  washCycle();

  pump(PUMP_PERMEABILIZATION, "Permeab.",   VOLUME_PERMEABILIZATION, FR_PERMEABILIZATION);
  incubate("Permeabilization", PAUSE_PERMEABILIZATION);
  washCycle();

  pump(PUMP_ANTIBODY1,        "Antibody 1", VOLUME_ANTIBODY1,        FR_ANTIBODY1);
  incubate("Antibody 1",       PAUSE_ANTIBODY1);
  washCycle();

  pump(PUMP_ANTIBODY2,        "Antibody 2", VOLUME_ANTIBODY2,        FR_ANTIBODY2);
  incubate("Antibody 2",       PAUSE_ANTIBODY2);
  washCycle();

  Serial.println("SEQ:end");
  lcd.clear();
  lcd.print("End of sequence");
  delay(30000);
  lcd.clear();
  lcd.print("Waiting for GUI...");
  sequenceRunning = false;
}

void loop() {

  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.startsWith("VOL:")) {
      parseVolumes(line);
    } else if (line == "START") {
      runSequence();
    } else if (line == "STOP") {
      turnOffAllPumps();
      sequenceRunning = false;
      Serial.println("ACK:stopped");
      lcd.clear();
      lcd.print("Stopped.");
    } else if (line == "DIAG") {
      
      for (int pin = 2; pin <= 7; pin++) {
        digitalWrite(pin, HIGH);
        delay(2000);
        digitalWrite(pin, LOW);
        delay(500);
      }
      Serial.println("ACK:diag_done");
    }
  }

  
  if (!sequenceRunning && digitalRead(BUTTON) == LOW) {
    delay(50); // debounce
    if (digitalRead(BUTTON) == LOW) {
      runSequence();
    }
  }
}
