// MINI DESK LIGHT BOX - a working 100 mm (4") version of the desk stand box, to test the
// whole system (glow, LED plate, bezel, screws, stand) in a few hours of printing.
// Wired (USB) only: a power bank doesn't fit at this size.
include <lightbox.scad>
od       = 100;
face_d   = 99;
window_d = 84;
cavity   = 25;
stand_extra = 12;
part = "assembly";   // body | led_plate | bezel | stand | assembly
demo_face_dir = "test/mini/";
demo_face_colours = ["141414", "f6cf14", "f5f5f2"];   // yellow S test face

if (part == "body") body(cable_angle = 270, mount_angle = 270);
else if (part == "led_plate") led_plate();
else if (part == "bezel") bezel();
else if (part == "stand") desk_stand();
else if (part == "assembly") {
    color("#3a3a3a") desk_stand();
    translate([0, body_h(false) / 2, 7 + R]) rotate([90, 0, 0]) dressed_body(cable_angle = 270, mount_angle = 270);
}
