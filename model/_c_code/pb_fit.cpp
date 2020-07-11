double pb_fitInto(double v, double upper) {
  if (v >= upper) {
    return v-upper;
  } else if (v < 0.) {
    return v+upper;
  } else {
    return v;
  }
}
