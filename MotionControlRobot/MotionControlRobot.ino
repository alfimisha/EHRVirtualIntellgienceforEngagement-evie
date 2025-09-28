//changed motion control based on the fact that there were NO MOTOR CONTROLS IN HIVE!!!!!
//used to use UART
const int motor1GatePin = 9;
const int motor2GatePin = 3;
const int faceRec = 13;

void setup() {
  pinMode(motor1GatePin, OUTPUT);
  pinMode(motor2GatePin, OUTPUT);
  pinMode(faceRec, INPUT);

}

void loop() {
  if (!digitalRead(faceRec)) {
    digitalWrite(motor1GatePin, LOW);  // Gate = 0V -> PMOS ON
    digitalWrite(motor2GatePin, LOW);  // Gate = 0V -> PMOS ON
    
  } else {
    digitalWrite(motor1GatePin, HIGH); // Gate = +5V -> PMOS OFF
    digitalWrite(motor2GatePin, HIGH);
    exit(0);
  }
}
