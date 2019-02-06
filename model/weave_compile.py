import numpy as np
from weave import ext_tools

def weave_compile():
    #---------------------Specify variable types---------------------
    params = {'Gradient Intensity': [0.0, 0.0, 1.52],
        'Cell Density': 0.5,
        'Angular Inertia': 2.5284,
        'Alignment Strength': 1.5284,
        'Pinned Cells': ['none', 'none', 'none'],
        'Gradient Angle': [0.79, 0.47, 1.83],
        'Alignment Range': 11.1,
        'Affinity': [[3.25, 1.13, 1.15], [1.13, 1.36, 4.0], [1.15, 4.0, 1.48]],
        'Attraction-Repulsion Strength': 4.7298,
        'Cell Ratio': [0.5, 0.5, 0.],
        'Noise Intensity': 0.28,
        'Velocity': [0.034, 0.016, 0.169],
        'Attraction-Repulsion Range': 10.2}

    sf = 1.2
    size_x = 10.
    size_y = 10.
    r0 = 0.15*sf
    r0_x_2 = r0 * 2
    n = int(params["Cell Density"]*(size_x*size_y)/(2*(3**0.5)*r0*r0))
    noise_coef=params["Noise Intensity"]
    iner_coef = params["Angular Inertia"]
    r1 = params["Attraction-Repulsion Range"]*r0
    rv = params["Alignment Range"]*r0
    f0 = params["Attraction-Repulsion Strength"]
    fa = params["Alignment Strength"]
    v0 = np.array(params["Velocity"])*sf
    beta = np.array(params["Affinity"])
    cutoff = np.array([n/2, n+1]).astype(np.int32)
    grad_x = np.array([np.cos(d*np.pi) * i for d, i in zip(params["Gradient Angle"], params["Gradient Intensity"])])
    grad_y = np.array([np.sin(d*np.pi) * i for d, i in zip(params["Gradient Angle"], params["Gradient Intensity"])])
    pinned = np.array([0 if x == "none" else 1 for x in params["Pinned Cells"]]).astype(np.int32)

    pos_x = np.random.random(n)*size_x
    pos_y = np.random.random(n)*size_y

    dir_x = np.zeros(n)
    dir_y = np.zeros(n)

    #---------------------C file name---------------------
    mod = ext_tools.ext_module('c_code')

    #---------------------Main code---------------------

    fb_dist = """
    double fb_dist(double x1, double y1, double x2, double y2) {
        double r = sqrt(pow((x1-x2),2) + pow((y1-y2),2));
        return r;
    }
    """


    fb_fit = """
    double fb_fitInto(double v, double upper) {
        if (v > upper) {
            return upper;
        } else if (v < 0.) {
            return 0.;
        } else {
            return v;
        }
    }
    """
    fb_main_code = """
    int i, j, k, k2, start_index, end_index, start_index2, end_index2;
    float grad_i_x, grad_i_y, align_i_x, align_i_y, f_i_x, f_i_y;
    float beta_ij, ar_slope, ar_interc, r, temp, noise, c, s, v0_i;

    // UPDATE DIRECTION
    start_index = 0;
    for (k = 0; k < 3; k++) {
      end_index = cutoff[k];

      if (pinned[k] == 0) {
        // Only if i is not pinned

        // GRADIENT (constant across same species)
        grad_i_x = grad_x[k];
        grad_i_y = grad_y[k];

        for (i = start_index; i < end_index; i++) {
          // INITIALIZATION
          // Alignment term
          align_i_x = 0;
          align_i_y = 0;
          // A-R term
          f_i_x = 0;
          f_i_y = 0;

          start_index2 = 0;
          for (k2 = 0; k2 < 3; k2++) {
            end_index2 = cutoff[k2];

            beta_ij = beta[k*3 + k2];
            ar_slope = (1 + beta_ij) * f0 / (r1 - r0_x_2);
            ar_interc = - r0_x_2 * (1 + beta_ij) * f0 / (r1 - r0_x_2) - f0;

            for (j = start_index2; j < end_index2; j++) {
              if (i != j) {
                r = fb_dist(pos_x[i], pos_y[i], pos_x[j], pos_y[j]);
                // ALIGNMENT
                if (pinned[k2] == 0) {
                  // Only if j is not pinned
                  if (r <= rv) {
                    align_i_x += dir_x[j];
                    align_i_y += dir_y[j];
                  }
                }
                // ATTRACTION-REPULSION
                if (r <= r1) {
                  if (r < r0_x_2) {
                    // Infinite repulsion
                    f_i_x += -10000 * (pos_x[j] - pos_x[i]);
                    f_i_y += -10000 * (pos_y[j] - pos_y[i]);
                  } else {
                    // Equilibrium attraction and repulsion
                    temp = r * ar_slope + ar_interc;
                    f_i_x += temp * (pos_x[j] - pos_x[i]) / r;
                    f_i_y += temp * (pos_y[j] - pos_y[i]) / r;
                  }
                }
              }
            }
          start_index2 = end_index2;
          }

          // INERTIA
          dir_x[i] *= iner_coef;
          dir_y[i] *= iner_coef;

          // ADD OTHER TERMS
          dir_x[i] += grad_i_x + align_i_x + f_i_x;
          dir_y[i] += grad_i_y + align_i_y + f_i_y;

          // NORMALIZE (ARG)
          temp = sqrt(pow(dir_x[i], 2) + pow(dir_y[i], 2));
          if (temp > 0) {
            //Avoid dividing by zero
            dir_x[i] /= temp;
            dir_y[i] /= temp;
          }

          // NOISE
          noise = noise_coef*M_PI*((static_cast <float> (rand()) / static_cast <float> (RAND_MAX))*2-1);
          c = cos(noise);
          s = sin(noise);
          temp = dir_x[i];
          dir_x[i] = dir_x[i]*c - dir_y[i]*s;
          dir_y[i] = temp*s + dir_y[i]*c;
        }
      }
      start_index = end_index;
    }

    // UPDATE POSITION
    start_index = 0;
    for (k = 0; k < 3; k++) {
      end_index = cutoff[k];

      if (pinned[k] == 0) {
        // Only if the cell type is not pinned

        // SPEED (constant across same species)
        v0_i = v0[k];

        for (i = start_index; i < end_index; i++) {
          pos_x[i] += v0_i * dir_x[i];
          pos_x[i] = fb_fitInto(pos_x[i], size_x);
          pos_y[i] += v0_i * dir_y[i];
          pos_y[i] = fb_fitInto(pos_y[i], size_y);
        }
      }

      start_index = end_index;
    }
    """

    pb_dist = """
    double pb_dist(double x1, double x2, double size_x) {
        double x = x2-x1;
        if (x > size_x/2.){
        x -= size_x;
        } else if (x < -size_x/2.){
        x += size_x;
        }

        return x;
    }
    """

    pb_fit = """
    double pb_fitInto(double v, double upper) {
        if (v >= upper) {
            return v-upper;
        } else if (v < 0.) {
            return v+upper;
        } else {
            return v;
        }
    }
    """

    pb_main_code = """
    int i, j, k, k2, start_index, end_index, start_index2, end_index2;
    float grad_i_x, grad_i_y, align_i_x, align_i_y, f_i_x, f_i_y;
    float beta_ij, ar_slope, ar_interc, r, temp, noise, c, s, v0_i, dis_x, dis_y;
    // UPDATE DIRECTION
    start_index = 0;
    for (k = 0; k < 3; k++) {
      end_index = cutoff[k];

      if (pinned[k] == 0) {
        // Only if i is not pinned

        // GRADIENT (constant across same species)
        grad_i_x = grad_x[k];
        grad_i_y = grad_y[k];

        for (i = start_index; i < end_index; i++) {
          // INITIALIZATION
          // Alignment term
          align_i_x = 0;
          align_i_y = 0;
          // A-R term
          f_i_x = 0;
          f_i_y = 0;

          start_index2 = 0;
          for (k2 = 0; k2 < 3; k2++) {
            end_index2 = cutoff[k2];

            beta_ij = beta[k*3 + k2];
            ar_slope = (1 + beta_ij) * f0 / (r1 - r0_x_2);
            ar_interc = - r0_x_2 * (1 + beta_ij) * f0 / (r1 - r0_x_2) - f0;

            for (j = start_index2; j < end_index2; j++) {
              if (i != j) {
                dis_x = pb_dist(pos_x[i], pos_x[j], size_x);
                dis_y = pb_dist(pos_y[i], pos_y[j], size_y);
                r = sqrt(pow(dis_x,2)+pow(dis_y,2));

                // ALIGNMENT
                if (pinned[k2] == 0) {
                  // Only if j is not pinned
                  if (r <= rv) {
                    align_i_x += dir_x[j];
                    align_i_y += dir_y[j];
                  }
                }
                // ATTRACTION-REPULSION
                if (r <= r1) {
                  if (r < r0_x_2) {
                    // Infinite repulsion
                    f_i_x += -10000 * dis_x;
                    f_i_y += -10000 * dis_y;
                  } else {
                    // Equilibrium attraction and repulsion
                    temp = r * ar_slope + ar_interc;
                    f_i_x += temp * dis_x / r;
                    f_i_y += temp * dis_y / r;
                  }
                }
              }
            }
          start_index2 = end_index2;
          }

          // INERTIA
          dir_x[i] *= iner_coef;
          dir_y[i] *= iner_coef;

          // ADD OTHER TERMS
          dir_x[i] += grad_i_x + align_i_x + f_i_x;
          dir_y[i] += grad_i_y + align_i_y + f_i_y;

          // NORMALIZE (ARG)
          temp = sqrt(pow(dir_x[i], 2) + pow(dir_y[i], 2));
          if (temp > 0) {
            //Avoid dividing by zero
            dir_x[i] /= temp;
            dir_y[i] /= temp;
          }

          // NOISE
          noise = noise_coef*M_PI*((static_cast <float> (rand()) / static_cast <float> (RAND_MAX))*2-1);
          c = cos(noise);
          s = sin(noise);
          temp = dir_x[i];
          dir_x[i] = dir_x[i]*c - dir_y[i]*s;
          dir_y[i] = temp*s + dir_y[i]*c;
        }
      }
      start_index = end_index;
    }

    // UPDATE POSITION
    start_index = 0;
    for (k = 0; k < 3; k++) {
      end_index = cutoff[k];

      if (pinned[k] == 0) {
        // Only if the cell type is not pinned

        // SPEED (constant across same species)
        v0_i = v0[k];

        for (i = start_index; i < end_index; i++) {
          pos_x[i] += v0_i * dir_x[i];
          pos_x[i] = pb_fitInto(pos_x[i], size_x);
          pos_y[i] += v0_i * dir_y[i];
          pos_y[i] = pb_fitInto(pos_y[i], size_y);
        }
      }

      start_index = end_index;
    }
    """

    fb_tick_func = ext_tools.ext_function('fb_tick',fb_main_code,
                    ["n","size_x", "size_y","r0_x_2","r1","rv",
                     "iner_coef", "f0","fa", "noise_coef", "v0", "pinned",
                       "cutoff", "beta", "grad_x", "grad_y",
                       "pos_x","pos_y","dir_x","dir_y"])
    fb_tick_func.customize.add_support_code(fb_dist)
    fb_tick_func.customize.add_support_code(fb_fit)
    fb_tick_func.customize.add_header("<math.h>")
    mod.add_function(fb_tick_func)


    pb_tick_func = ext_tools.ext_function('pb_tick',pb_main_code,
                    ["n","size_x", "size_y","r0_x_2","r1","rv",
                     "iner_coef", "f0","fa", "noise_coef", "v0", "pinned",
                       "cutoff", "beta", "grad_x", "grad_y",
                       "pos_x","pos_y","dir_x","dir_y"])
    pb_tick_func.customize.add_support_code(pb_dist)
    pb_tick_func.customize.add_support_code(pb_fit)
    pb_tick_func.customize.add_header("<math.h>")
    mod.add_function(pb_tick_func)

    mod.compile(compiler="gcc", verbose=0)

if __name__ == "__main__":
    weave_compile()
