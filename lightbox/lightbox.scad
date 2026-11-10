// Round light box system for printed sign faces - Bambu Lab P1S (256 mm bed).
//
// Every style uses the SAME face disc, bezel and "cup" body, so any printed face
// fits any box:
//   wall_flat.scad        flat on the wall, facing forward, one face
//   wall_projecting.scad  sticks out sideways from the wall, two faces (or one + blank)
//   desk_stand.scad       stands on a shelf/desk in a cradle base, one face
// Each style can be wall-powered (USB cable) or battery-powered (a USB power bank).
//
// Units: mm. Pick the part with  part = "...";  (or  openscad -D 'part="bezel"' ...).
// This file is the library; open one of the style files above, not this one.

// ------------------------------------------------------------ shared sizes
od        = 240;    // body outside diameter (bezel adds ~6 mm)
wall      = 2.4;    // body wall
face_d    = 239;    // printed face disc (face.py --disc)
face_t    = 1.6;    // printed face thickness (face.py skin + back)
window_d  = 224;    // visible opening in the bezel (face.py --window)
clear     = 0.3;    // sliding clearance
bezel_wall  = 2.4;
bezel_lip   = 2.0;  // front lip thickness
bezel_skirt = 10;   // how far the bezel slides down the body
cavity    = 40;     // LEDs to face. Deeper = more even light; 40 suits COB strip
back_t    = 2.4;    // body back
plate_t   = 2.0;    // LED plate
bay_min   = 6;      // gap behind the LED plate for wires / wall-screw heads

// power bank (battery versions). MEASURE YOURS: length (port end to far end), width, height
bank      = [100, 64, 16];
bank_port = [34, 0];   // opening for the bank's ports/button: width; 0 = use bank height

// M3 self-tapping screws (or #4 wood screws) everywhere
pilot     = 2.6;    // pilot hole the screw cuts its own thread in
screw_clear = 3.4;

mount_z   = 14;     // height of the cradle/arm screws and cable slot above the back
mount_sp  = 50;     // spacing of the two cradle/arm screws (around the rim)
cable_slot = [15, 9];  // fits a USB-A plug (around, along)
bezel_screw_angles = [90, 210, 330];

$fn = 240;

// ------------------------------------------------------------ derived
R     = od / 2;
IR    = R - wall;
BR    = R + clear + bezel_wall;                      // bezel outside radius
function bay(battery)   = battery ? bank[2] + 2 : bay_min;
function body_h(battery) = back_t + bay(battery) + plate_t + cavity;
function ang_off(d) = d / 2 / R * 180 / PI;           // half-spacing -> degrees

// ------------------------------------------------------------ helpers
module at_angle(a, z) { rotate([0, 0, a]) translate([R, 0, z]) children(); }

// radial hole through the wall at angle a, height z
module radial_hole(a, z, d, len = 3 * wall + 12) {
    at_angle(a, z) rotate([0, -90, 0]) translate([0, 0, -len / 2]) cylinder(d = d, h = len, $fn = 24);
}

module slot2d(w, h) {                      // rounded slot, w wide, h tall
    r = min(w, h) / 2;
    hull() for (s = [-1, 1]) translate(w > h ? [s * (w / 2 - r), 0] : [0, s * (h / 2 - r)]) circle(r, $fn = 24);
}

module radial_slot(a, z, w, h) {
    at_angle(a, z) rotate([0, 90, 0]) rotate([0, 0, 90])
        linear_extrude(3 * wall + 12, center = true) slot2d(w, h);
}

// ------------------------------------------------------------ BODY ("cup")
// Printed open side up, back on the plate, no supports.
//   battery      : true = power-bank bay behind the LED plate, port opening at port_angle
//   cable_angle  : USB cable slot through the side wall (undef = none)
//   mount_angle  : two screw holes for the desk cradle / projecting arm (undef = none)
//   keyholes     : two keyhole slots in the back for hanging flat on the wall
//   join         : 4 bolt holes + wire hole in the back to bolt two cups back to back
module body(battery = false, port_angle = 270, cable_angle = undef, mount_angle = undef,
            keyholes = false, join = false) {
    H  = body_h(battery);
    zp = back_t + bay(battery);                       // underside of LED plate
    port_h = bank_port[1] > 0 ? bank_port[1] : bank[2] + 1;
    port_halfang = ang_off(bank[1] + 12);
    difference() {
        union() {
            // shell, small chamfer on the back edge
            difference() {
                hull() {
                    cylinder(r = R - 1, h = 1);
                    translate([0, 0, 1]) cylinder(r = R, h = H - 1);
                }
                translate([0, 0, back_t]) cylinder(r = IR, h = H);
            }
            // 45-degree ledge the LED plate rests on (cut away where the bank sits)
            difference() {
                rotate_extrude($fn = 240)
                    polygon([[IR + 0.01, zp - 3], [IR + 0.01, zp], [IR - 3, zp]]);
                if (battery) rotate([0, 0, port_angle])
                    rotate([0, 0, -port_halfang]) rotate_extrude(angle = 2 * port_halfang)
                        square([R, H]);
            }
            // bosses for the bezel screws (chamfered underneath so they print)
            for (a = bezel_screw_angles) rotate([0, 0, a])
                translate([IR, 0, H - 14]) hull() {
                    translate([-4.5, -5, 6]) cube([5, 10, 8]);
                    translate([-0.01, -5, 0]) cube([0.5, 10, 14]);
                }
            // battery: rails that keep the bank against the port opening
            if (battery) rotate([0, 0, port_angle])
                for (s = [-1, 1]) translate([IR - bank[0] - 2, s * (bank[1] / 2 + 1.2) - 1.2, back_t - 0.01])
                    cube([bank[0] + 2, 2.4, 6]);
            // join: thicker pads around the back bolts
            if (join) for (x = [-1, 1], y = [-1, 1]) translate([x * 45, y * 45, back_t - 0.01])
                cylinder(d = 9, h = 2, $fn = 32);
        }
        // bezel screw pilots
        for (a = bezel_screw_angles) radial_hole(a, H - 5, pilot);
        // cradle / arm screws (heads inside) + their cable slot
        if (mount_angle != undef) for (s = [-1, 1])
            radial_hole(mount_angle + s * ang_off(mount_sp), mount_z, screw_clear);
        if (cable_angle != undef) radial_slot(cable_angle, mount_z, cable_slot[0], cable_slot[1]);
        // battery: opening for the bank's charge port and button
        if (battery) at_angle(port_angle, back_t + port_h / 2)
            cube([4 * wall, bank_port[0], port_h], center = true);
        // keyholes for flat wall mounting (screw heads sit in the bay behind the LED plate)
        if (keyholes) for (x = [-60, 60]) translate([x, 55, -1]) {
            cylinder(d = 9.5, h = back_t + 2, $fn = 32);
            hull() for (y = [0, 10]) translate([0, y, 0]) cylinder(d = 4.6, h = back_t + 2, $fn = 24);
        }
        // join: bolt holes + wire pass-through between the two cups
        if (join) {
            for (x = [-1, 1], y = [-1, 1]) translate([x * 45, y * 45, -1]) cylinder(d = screw_clear, h = 10, $fn = 24);
            translate([0, 0, -1]) linear_extrude(back_t + 4) slot2d(cable_slot[0], cable_slot[1]);
        }
    }
}

// ------------------------------------------------------------ LED PLATE
// Drops in from the front and rests on the ledge. Print in WHITE: it is the reflector.
// The notch lets the strip's cable down into the bay; turn it to the cable slot.
module led_plate() {
    difference() {
        cylinder(r = IR - clear - 0.2, h = plate_t);
        translate([IR - 8, -9, -1]) cube([20, 18, plate_t + 2]);           // cable notch
        for (r = [95, 50]) for (a = [0 : 120 : 359])                         // tiny marks for
            rotate([0, 0, a]) translate([r, 0, plate_t - 0.4]) cylinder(d = 2, h = 1, $fn = 12); // the LED rings
    }
}

// ------------------------------------------------------------ BEZEL
// Printed front-down (looks best on the textured plate). Slides over the body and
// clamps the face; three M3 x 8 screws go in from the side.
module bezel() {
    pocket = bezel_lip + face_t + 0.2;
    h = pocket + bezel_skirt;
    difference() {
        hull() {
            cylinder(r = BR - 1, h = 1);
            translate([0, 0, 1]) cylinder(r = BR, h = h - 1);
        }
        translate([0, 0, -1]) cylinder(d = window_d, h = h + 2);
        translate([0, 0, -0.01]) cylinder(d1 = window_d + 2, d2 = window_d, h = 1);  // soft inner edge
        translate([0, 0, bezel_lip]) cylinder(r = R + clear, h = h);
        for (a = bezel_screw_angles) rotate([0, 0, a]) translate([R - 2, 0, pocket + 5])
            rotate([0, 90, 0]) cylinder(d = screw_clear, h = 10, $fn = 24);
    }
}

// Opaque disc for the unused side of a two-sided box. Print in any colour (black is classic).
module blank_face() { cylinder(d = face_d, h = face_t); }

// ------------------------------------------------------------ DESK CRADLE
// The cup lies in the cradle with its face toward -y. Two screws from inside the cup.
// battery: power-bank pocket in the base, it slides in from the right-hand side.
stand_w     = 160;
stand_extra = 18;     // how far the base reaches past the body, front and back
module desk_stand(battery = false, body_battery = false) {
    H  = body_h(body_battery);
    L  = H + 2 * stand_extra;
    hc = battery ? bank[2] + 7 : 7;          // base thickness under the lowest point of the body
    top = hc + 24;
    ymount = H / 2 - mount_z;                 // body back is at +y
    difference() {
        hull() for (x = [-1, 1], y = [-1, 1])
            translate([x * (stand_w / 2 - 8), y * (L / 2 - 8) + (y < 0 ? -4 : 0), 0])
                cylinder(r = 8, h = top, $fn = 48);
        // the body ...
        translate([0, 0, hc + R]) rotate([90, 0, 0]) cylinder(r = R + clear, h = L + 20, center = true);
        // ... and the bezel at its front
        translate([0, -H / 2 + bezel_skirt + 0.5, hc + R]) rotate([90, 0, 0])
            cylinder(r = BR + 0.5, h = L);
        // screws: pilots on the same radial lines as the holes in the body
        for (s = [-1, 1]) translate([0, ymount, hc + R]) rotate([0, s * ang_off(mount_sp), 0])
            translate([0, 0, -R - 12]) cylinder(d = pilot, h = 14, $fn = 24);
        // cable from the body's slot down into the base
        translate([0, ymount, 0]) linear_extrude(hc + 5) rotate(90) slot2d(cable_slot[1], cable_slot[0]);
        if (battery) {
            // bank pocket, open on the right (+x) so the bank slides in, ports outward
            translate([stand_w / 2 - bank[0] - 1, -bank[1] / 2 - 0.5, 2.5])
                cube([bank[0] + 10, bank[1] + 1, bank[2] + 1]);
        } else {
            // cable channel underneath, out the back
            translate([-5, ymount - 5, -1]) cube([10, L, 5]);
        }
        // recesses for stick-on rubber feet
        for (x = [-1, 1], y = [-1, 1]) translate([x * (stand_w / 2 - 16), y * (L / 2 - 14), -1])
            cylinder(d = 10.5, h = 1.6, $fn = 32);
    }
}

// ------------------------------------------------------------ PROJECTING WALL ARM
// Two cups bolted back to back make a drum (axis horizontal, along the wall). The arm's
// curved pad takes 4 screws from inside the drum (2 per cup); the plate screws to the wall.
// The USB cable runs from the drum through the arm and out of a groove behind the plate.
arm_gap   = 35;       // gap between wall and drum
arm_h     = 70;       // pad height
wall_plate = [5, 0, 160];   // thickness, (width = auto), height
module wall_arm(h_a, h_b) {
    // h_a, h_b: body heights of the two cups (a: y < 0, b: y > 0); joint at y = 0
    y0 = -h_a + bezel_skirt + 2;  y1 = h_b - bezel_skirt - 2;
    X = R + arm_gap;                            // wall face of the arm
    tp = wall_plate[0];
    difference() {
        union() {
            // wall plate
            translate([-X - tp, y0, -wall_plate[2] / 2]) cube([tp, y1 - y0, wall_plate[2]]);
            // arm block
            difference() {
                translate([-X - 0.01, y0, -arm_h / 2]) cube([arm_gap + 18, y1 - y0, arm_h]);
                rotate([90, 0, 0]) cylinder(r = R + 0.2, h = 400, center = true);
            }
        }
        // screw pilots, radial, matching mount_angle = 180 on both cups
        for (yy = [-mount_z, mount_z], s = [-1, 1])
            translate([0, yy, 0]) rotate([0, s * ang_off(mount_sp), 0])
                translate([-R + 2, 0, 0]) rotate([0, -90, 0]) cylinder(d = pilot, h = 16, $fn = 24);
        // cable: from cup A's slot (y = -mount_z) straight through to the wall
        translate([-X - tp - 1, -mount_z, 0]) rotate([0, 90, 0])
            linear_extrude(arm_gap + tp + 10) slot2d(cable_slot[0] + 1, cable_slot[1] + 1);
        // groove on the wall side of the plate, down to the bottom edge
        translate([-X - tp - 1, -mount_z - 3, -wall_plate[2] / 2 - 1]) cube([3.5, 6, wall_plate[2] / 2 + 1]);
        // countersunk wall screws (#8 / 4 mm)
        for (z = [-1, 1]) translate([-X - tp - 0.01, (y0 + y1) / 2, z * (wall_plate[2] / 2 - 15)])
            rotate([0, 90, 0]) { cylinder(d = 4.5, h = 20, $fn = 24);
                                 translate([0, 0, tp - 3]) cylinder(d1 = 4.5, d2 = 9.5, h = 3.02, $fn = 24); }
    }
}

// ------------------------------------------------------------ assembly helpers
// Example face shown in the assembly views (only for looking at; not exported)
demo_face_dir = "../susquehanna-s/lightbox_face/";
demo_face_colours = ["141414", "f6cf14", "1f2f82", "f5f5f2", "d0202e"];
module face_front_up() {           // printed face, turned front-side up
    rotate([0, 180, 0]) translate([0, 0, -face_t])
        for (c = demo_face_colours) color(str("#", c)) import(str(demo_face_dir, "face_", c, ".stl"));
}
// a body with LED plate, face and bezel, front toward +z, back at z = 0
module dressed_body(battery = false, port_angle = 270, cable_angle = undef, mount_angle = undef,
                    keyholes = false, join = false, face = true, face_rot = 0) {
    H = body_h(battery);
    color("#2b2b2b") body(battery, port_angle, cable_angle, mount_angle, keyholes, join);
    color("white") translate([0, 0, back_t + bay(battery)]) led_plate();
    if (face) translate([0, 0, H]) rotate([0, 0, face_rot]) face_front_up();
    else color("#2b2b2b") translate([0, 0, H]) blank_face();
    color("#3a3a3a") translate([0, 0, H + face_t + 0.2 + bezel_lip]) mirror([0, 0, 1]) bezel();
}
