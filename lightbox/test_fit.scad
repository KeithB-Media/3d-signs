// FIT TEST - 60-degree slices of the full-size (240 mm) body rim, bezel and face.
// Tests the bezel slide fit, the face seat and one bezel screw, using ~25 g of filament.
include <lightbox.scad>
part = "all";   // body_arc | bezel_arc | face_arc

module wedge(h) rotate([0, 0, 60]) rotate_extrude(angle = 60) translate([0, -1]) square([BR + 5, h + 2]);

H = body_h(false);
module body_arc()  intersection() { translate([0, 0, -(H - 20)]) body(); wedge(20); }   // top 20 mm, with the screw boss at 90 deg
module bezel_arc() intersection() { bezel(); wedge(30); }
module face_arc()  intersection() { difference() { blank_face(); translate([0, 0, -1]) cylinder(r = R - 25, h = 5); } wedge(5); }

if (part == "body_arc") body_arc();
else if (part == "bezel_arc") bezel_arc();
else if (part == "face_arc") face_arc();
else { body_arc(); translate([0, -40, 0]) bezel_arc(); translate([0, -80, 0]) face_arc(); }
