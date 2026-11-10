// DESK / SHELF light box - the round box sits in a cradle base. One printed face.
//
// Print: body, led_plate (white), bezel, stand, + your face (face.py).
// The body is joined to the stand by 2 screws from inside (take the face off to reach them).
// Wired: USB cable goes down through the stand and out a channel underneath, at the back.
// Battery: the power bank slides into the stand from the right; plug the LED cable into it.
include <lightbox.scad>

battery = false;      // true = stand with a power-bank pocket
part = "assembly";    // body | led_plate | bezel | stand | assembly

if (part == "body") body(cable_angle = 270, mount_angle = 270);
else if (part == "led_plate") led_plate();
else if (part == "bezel") bezel();
else if (part == "stand") desk_stand(battery = battery);
else if (part == "assembly") {
    H = body_h(false);
    hc = battery ? bank[2] + 7 : 7;
    color("#3a3a3a") desk_stand(battery = battery);
    translate([0, H / 2, hc + R]) rotate([90, 0, 0])
        dressed_body(cable_angle = 270, mount_angle = 270);
}
