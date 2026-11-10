// PROJECTING (sideways) WALL light box - sticks out from the wall like a shop sign,
// readable from both directions. Two printed faces, or one face + a blank disc.
//
// It is two bodies bolted back to back (4 x M3 x 10 + nuts), hung on the arm.
// Print: body_a, body_b, 2 x led_plate (white), 2 x bezel, arm,
//        + 2 faces (or 1 face + blank_face).
// Wired: USB cable runs from body A through the arm and down a groove behind the wall plate.
// Battery: power bank in body A behind its LED plate, ports at the bottom.
// The wire for body B's LEDs passes through the hole in the middle of the two backs.
include <lightbox.scad>

battery = false;      // true = body A has the power-bank bay
part = "assembly";    // body_a | body_b | led_plate | bezel | blank_face | arm | assembly

// both cups: arm screws at 180 deg. Body B is turned over (about x), so it keeps 180.
module body_a() body(battery = battery, port_angle = 270, cable_angle = battery ? undef : 180,
                     mount_angle = 180, join = true);
module body_b() body(mount_angle = 180, join = true);

if (part == "body_a") body_a();
else if (part == "body_b") body_b();
else if (part == "led_plate") led_plate();
else if (part == "bezel") bezel();
else if (part == "blank_face") blank_face();
else if (part == "arm") wall_arm(body_h(false), body_h(false));
else if (part == "arm_print")                       // wall plate down on the bed
    translate([0, 0, R + arm_gap + wall_plate[0]]) rotate([0, -90, 0]) wall_arm(body_h(false), body_h(false));
else if (part == "assembly") {
    color("#3a3a3a") wall_arm(body_h(false), body_h(false));
    // body A: front toward -y; body B: front toward +y
    rotate([90, 0, 0]) dressed_body(battery = battery, port_angle = 270,
        cable_angle = battery ? undef : 180, mount_angle = 180, join = true);
    rotate([-90, 0, 0]) dressed_body(mount_angle = 180, join = true, face_rot = 180);
    // the wall
    color("#cfc8bb") translate([-R - arm_gap - wall_plate[0] - 2, -170, -170]) cube([2, 340, 340]);
}
