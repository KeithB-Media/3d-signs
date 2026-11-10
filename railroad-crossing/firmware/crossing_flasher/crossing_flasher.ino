/*
  Railroad crossing flasher – alternating red lamps with an incandescent-style fade.

  Board: ATtiny85 (ATTinyCore, 8 MHz internal) or a Digispark. Also runs on an
  Arduino Nano/Uno; see the pin settings below.

  Battery: 3 x AA (4.5 V) holder with switch, wired straight to VCC/GND.
           (On a Digispark, connect the battery + to the "5V" pin, NOT "VIN".)

  Wiring (ATtiny85 DIP-8 pin numbers):
    pin 8 VCC  -> battery +            pin 4 GND -> battery -
    pin 5 PB0  -> 180R -> left LED  + (LED - to GND)
    pin 6 PB1  -> 180R -> right LED + (LED - to GND)
    pin 7 PB2  -> push button -> GND          (optional)
    pin 3 PB4  -> passive piezo -> GND        (optional crossing bell)

  Behaviour:
    * Switch on: lamps flash for RUN_MINUTES, then the chip sleeps (~1 uA).
    * Push button: start / stop. A press also wakes it from sleep.
    * Set RUN_MINUTES to 0 to flash for as long as the power is on.
*/
#include <avr/sleep.h>
#include <avr/interrupt.h>

// ----------------------------------------------------------------- settings
const uint8_t  LAMP_L = 0;          // PB0 (PWM)   Nano/Uno: use 5
const uint8_t  LAMP_R = 1;          // PB1 (PWM)   Nano/Uno: use 6
const uint8_t  BUTTON = 2;          // PB2         Nano/Uno: use 2
const uint8_t  BELL   = 4;          // PB4         Nano/Uno: use 8
const bool     USE_BELL     = false; // true if a piezo is fitted
const uint16_t FLASHES_PER_MIN = 45; // per lamp (real signals: 35-65)
const uint16_t FADE_MS      = 110;  // lamp warm-up / cool-down time
const uint8_t  BRIGHTNESS   = 255;  // 0-255
const uint16_t RUN_MINUTES  = 10;   // 0 = never time out
const uint16_t BELL_HZ      = 1350;
const uint16_t BELL_EVERY_MS = 480;

// ------------------------------------------------------------------ state
volatile bool woke = false;
bool running = true;
unsigned long startedAt;

ISR(PCINT0_vect) { woke = true; }   // ATtiny85 pin-change wake (button)

void lamps(uint8_t l, uint8_t r) {
  analogWrite(LAMP_L, l);
  analogWrite(LAMP_R, r);
}

// brightness of one lamp at time t (ms) inside its half-cycle
uint8_t level(unsigned long t, unsigned long half) {
  if (t >= half) return 0;
  float k = 1.0;
  if (t < FADE_MS) k = (float)t / FADE_MS;                 // warm up
  else if (t > half - FADE_MS) k = (float)(half - t) / FADE_MS; // cool down
  return (uint8_t)(BRIGHTNESS * k * k);                     // eye-friendly curve
}

bool buttonPressed() {
  static bool last = HIGH;
  static unsigned long changed = 0;
  bool now = digitalRead(BUTTON);
  if (now != last && millis() - changed > 40) {
    changed = millis();
    last = now;
    return now == LOW;
  }
  return false;
}

void goToSleep() {
  lamps(0, 0);
  if (USE_BELL) noTone(BELL);
  while (digitalRead(BUTTON) == LOW) {}   // wait for release
  delay(50);
#if defined(__AVR_ATtiny85__)
  GIMSK |= _BV(PCIE);
  PCMSK |= _BV(BUTTON);
  ADCSRA &= ~_BV(ADEN);                  // ADC off
  set_sleep_mode(SLEEP_MODE_PWR_DOWN);
  woke = false;
  sleep_enable();
  sei();
  sleep_cpu();                            // ... zzz until the button is pressed
  sleep_disable();
  PCMSK &= ~_BV(BUTTON);
  ADCSRA |= _BV(ADEN);
#else
  while (digitalRead(BUTTON) == HIGH) {}  // other boards: just wait
#endif
  while (digitalRead(BUTTON) == LOW) {}
  delay(50);
  running = true;
  startedAt = millis();
}

void setup() {
  pinMode(LAMP_L, OUTPUT);
  pinMode(LAMP_R, OUTPUT);
  pinMode(BUTTON, INPUT_PULLUP);
  if (USE_BELL) pinMode(BELL, OUTPUT);
  startedAt = millis();
}

void loop() {
  if (buttonPressed()) running = !running;
  if (RUN_MINUTES && millis() - startedAt > RUN_MINUTES * 60000UL) running = false;
  if (!running) { goToSleep(); return; }

  const unsigned long half = 30000UL / FLASHES_PER_MIN;    // ms each lamp is lit
  unsigned long t = (millis() - startedAt) % (2 * half);
  if (t < half) lamps(level(t, half), 0);
  else          lamps(0, level(t - half, half));

  if (USE_BELL) {                                           // short "ding" strikes
    unsigned long b = (millis() - startedAt) % BELL_EVERY_MS;
    if (b < 45) tone(BELL, BELL_HZ); else noTone(BELL);
  }
}
