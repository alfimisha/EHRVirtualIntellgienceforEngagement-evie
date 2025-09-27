// Arduino Robot Motor Control with commands from Intel Edison
const int AIN1 = 7;
const int AIN2 = 8;
const int PWMA = 9;   // PWM pin
const int BIN1 = 4;
const int BIN2 = 5;
const int PWMB = 6;   // PWM pin

String inputCommand = "";
const int MAX_COMMAND_LENGTH = 50; // Prevent buffer overflow

void setup() {
  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(PWMA, OUTPUT);
  pinMode(BIN1, OUTPUT);
  pinMode(BIN2, OUTPUT);
  pinMode(PWMB, OUTPUT);
  Serial.begin(9600); // Listen to Edison
  Serial.println("Robot ready for commands");
}

void driveLeft(int speed) {
  if (speed > 0) {
    digitalWrite(AIN1, HIGH);
    digitalWrite(AIN2, LOW);
  } else if (speed < 0) {
    digitalWrite(AIN1, LOW);
    digitalWrite(AIN2, HIGH);
    speed = -speed;
  } else {
    digitalWrite(AIN1, LOW);
    digitalWrite(AIN2, LOW); // brake
  }
  analogWrite(PWMA, constrain(speed, 0, 255));
}

void driveRight(int speed) {
  if (speed > 0) {
    digitalWrite(BIN1, HIGH);
    digitalWrite(BIN2, LOW);
  } else if (speed < 0) {
    digitalWrite(BIN1, LOW);
    digitalWrite(BIN2, HIGH);
    speed = -speed;
  } else {
    digitalWrite(BIN1, LOW);
    digitalWrite(BIN2, LOW); // brake
  }
  analogWrite(PWMB, constrain(speed, 0, 255));
}

void moveRobot(String dir, int duration, int speed = 200) {
  // Validate direction
  if (!(dir == "forward" || dir == "backward" || dir == "left" || 
        dir == "right" || dir == "stop")) {
    Serial.println("ERROR: Invalid direction");
    return;
  }
  
  // Validate speed and duration
  speed = constrain(speed, 0, 255);
  duration = constrain(duration, 0, 10000); // Max 10 seconds
  
  if (dir == "forward") {
    driveLeft(speed);
    driveRight(speed);
  } else if (dir == "backward") {
    driveLeft(-speed);
    driveRight(-speed);
  } else if (dir == "left") {
    driveLeft(-speed);
    driveRight(speed);
  } else if (dir == "right") {
    driveLeft(speed);
    driveRight(-speed);
  } else if (dir == "stop") {
    driveLeft(0);
    driveRight(0);
  }
  
  if (duration > 0) {
    delay(duration);
    driveLeft(0);
    driveRight(0);
  }
}

void parseAndExecuteCommand(String command) {
  command.trim(); // Remove whitespace
  
  if (command.length() == 0) return;
  
  // Find spaces to separate parameters
  int firstSpace = command.indexOf(' ');
  
  if (firstSpace == -1) {
    // Only direction provided (for continuous movement or stop)
    String dir = command;
    if (dir == "stop") {
      moveRobot(dir, 0);
    } else {
      Serial.println("ERROR: Missing duration parameter");
    }
    return;
  }
  
  String dir = command.substring(0, firstSpace);
  String remainder = command.substring(firstSpace + 1);
  
  int secondSpace = remainder.indexOf(' ');
  
  if (secondSpace == -1) {
    // Format: "direction duration"
    int duration = remainder.toInt();
    moveRobot(dir, duration);
  } else {
    // Format: "direction duration speed"
    int duration = remainder.substring(0, secondSpace).toInt();
    int speed = remainder.substring(secondSpace + 1).toInt();
    moveRobot(dir, duration, speed);
  }
}

void loop() {
  // Check if Edison sent a line
  if (Serial.available()) {
    char c = Serial.read();
    
    if (c == '\n' || c == '\r') { // end of command
      if (inputCommand.length() > 0) {
        parseAndExecuteCommand(inputCommand);
        inputCommand = ""; // clear buffer
      }
    } else if (c >= 32 && c <= 126) { // printable characters only
      if (inputCommand.length() < MAX_COMMAND_LENGTH) {
        inputCommand += c; // build up command string
      } else {
        Serial.println("ERROR: Command too long");
        inputCommand = ""; // reset buffer
      }
    }
    // Ignore other characters (control chars, etc.)
  }
}