double fb_fitInto(double v, double upper) {
  if (v > upper) {
    return upper;
  } else if (v < 0.) {
    return 0.;
  } else {
    return v;
  }
}
