double pb_dist(double x1, double x2, double size_x) {
  double x = x2-x1;
  if (x > size_x/2.){
    x -= size_x;
  } else if (x < -size_x/2.){
    x += size_x;
  }

  return x;
}
