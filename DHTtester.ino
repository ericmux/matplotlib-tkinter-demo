#include "DHT.h"
#define DHTPIN 38     // what digital pin we're connected to
#define hum_solo A8

#define DHTTYPE DHT11   // DHT 11


// Connect pin 1 (on the left) of the sensor to +5V
// NOTE: If using a board with 3.3V logic like an Arduino Due connect pin 1
// to 3.3V instead of 5V!
// Connect pin 2 of the sensor to whatever your DHTPIN is 
// Connect pin 4 (on the right) of the sensor to GROUND
// Connect a 10K resistor from pin 2 (data) to pin 1 (power) of the sensor

DHT dht(DHTPIN, DHTTYPE);
int valor_hum;
byte temprate = 30;
byte humrate = 30;
byte humsrate = 30;
byte tempcounter = 0;
byte humcounter = 0;
byte humscounter = 0;
int aux = 1;
byte start = 6;
byte command = 100;
byte t;
byte h;
unsigned int hums;
byte buf[2];


void setup() {
  Serial.begin(19200);
  Serial.println("DHTxx test!");
  pinMode(hum_solo, INPUT);

  
  
  while(true){
    delay(1000);
    Serial.write(start);
    if(Serial.available() > 0){
      aux = Serial.read();
      if(aux == 0){
        Serial.write(start);
        break;
      }
    }
  }
  
  dht.begin();
}

void loop() {
  
  // Wait a few seconds between measurements.
  delay(1000);
  if (tempcounter % temprate == 0){
    t = (byte) dht.readTemperature();
  }
  if (humcounter % humrate == 0){
    h = (byte) dht.readHumidity();
  }
  if (humscounter % humsrate == 0){
    hums = analogRead(hum_solo);
    buf[0] = hums & 255;
    buf[1] = (hums >> 8)  & 255;
  }
  
  if (tempcounter % temprate == 0){ 
    Serial.write(t);
  }
  if (humcounter % humrate == 0){ 
    Serial.write(h);
  }
  if (humscounter % humsrate == 0){ 
    Serial.write(buf, sizeof(buf));
  }

  tempcounter += 1;
  humcounter += 1;
  humscounter += 1;

  if(Serial.available()){
    command = Serial.read();
    if(command == 5){
      restart();
    }
    else if(command == 1){
      t = (byte) dht.readTemperature();
      h = (byte) dht.readHumidity(); 
      hums = analogRead(hum_solo);
      buf[0] = hums & 255;
      buf[1] = (hums >> 8)  & 255;
      Serial.write(t);
      Serial.println();
      Serial.write(h);
      Serial.println();
      Serial.write(buf, sizeof(buf));
      Serial.println();
//      maybe restart counters
    }
    else if(command == 2){
      while(!Serial.available()){}
      temprate = Serial.read();
      tempcounter = 1;
    }
    else if(command == 3){
      while(!Serial.available()){}
      humrate = Serial.read();
      humcounter = 1;
    }
    else if(command == 4){
      while(!Serial.available()){}
      humsrate = Serial.read();
      humscounter = 1;
    }
  }
}

void restart(){
  temprate = 30;
  humrate = 30;
  humsrate = 30;
  tempcounter = 0;
  humcounter = 0;
  humscounter = 0;
  while(true){
    delay(1000);
    Serial.write(start);
    if(Serial.available() > 0){
      aux = Serial.read();
      if(aux == 0){
        Serial.write(start);
        break;
      }
    }
  }
}

//  valor_hum = analogRead(hum_solo);  
//  // Reading temperature or humidity takes about 250 milliseconds!
//  // Sensor readings may also be up to 2 seconds 'old' (its a very slow sensor)
//  byte h = (byte) dht.readHumidity();
//  // Read temperature as Celsius (the default)
//  byte t = (byte) dht.readTemperature();
//  byte f = (byte) dht.readTemperature(true);
//  // Read temperature as Fahrenheit (isFahrenheit = true)
//  // Check if any reads failed and exit early (to try again).
//  if (isnan(h) || isnan(t)) {
//    Serial.println("Failed to read from DHT sensor!");
//    return;
//  }
//  // Compute heat index in Celsius (isFahreheit = false)
//  float hic = dht.computeHeatIndex(t, h, false);
//
//  Serial.print("Humidity: ");
//  Serial.print(h);
//  Serial.print(" %\t");
//  Serial.print("Temperature: ");
//  Serial.print(t);
//  Serial.print(" *C ");
////  Serial.print("Temperature: ");
////  Serial.print(f);
////  Serial.print(" *F ");
////  Serial.print("Heat index: ");
////  Serial.print(hic);
////  Serial.print(" *C ");
//  Serial.print("Umidade Solo analog: ");
//  Serial.print(hums);
//  Serial.println();
//}
