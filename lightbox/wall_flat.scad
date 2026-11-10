// FLAT WALL light box - hangs on two screws, face forward. One printed face.
//
// Print: body, led_plate (white), bezel, + your face (face.py).
// Wired: USB cable leaves through the slot at the bottom.
// Battery: a USB power bank lies behind the LED plate; its ports show through the
//          opening at the bottom. Set the bank size in lightbox.scad first.
include <lightbox.scad>

battery = false;      // true = power-bank version (deeper body)
part = "assembly";    // body | led_plate | bezel | assembly

module this_body() body(battery = battery, port_angle = 270,
                        cable_angle = battery ? undef : 270, keyholes = true);

if (part == "body") this_body();
else if (part == "led_plate") led_plate();
else if (part == "bezel") bezel();
else if (part == "assembly") rotate([90, 0, 0])
    dressed_body(battery = battery, port_angle = 270, cable_angle = battery ? undef : 270, keyholes = true);
