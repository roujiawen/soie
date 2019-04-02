"""This module contains C++ code that underlies the simulation as well as
Python commands to compile the C++ code through scipy.weave.
"""

import numpy as np
from weave import ext_tools

from common.parameters import N_GLOBAL_STATS


def weave_compile():
    """Compile C++ simulation code using numpy.weave so that it can be used in
    the Python program. Generate c_code.so file.
    """
    # ---------------------Specify variable types--------------------
    # The parameters below are used only to specify the types of variables
    # when compiling the C++ code, and does not affect the actual application
    # when it's run.
    params = {
        'Gradient Intensity': [0.0, 0.0, 1.52],
        'Cell Density': 0.5,
        'Angular Inertia': 2.5284,
        'Alignment Strength': 1.5284,
        'Pinned Cells': ['none', 'none', 'none'],
        'Gradient Angle': [0.79, 0.47, 1.83],
        'Alignment Range': 11.1,
        'Affinity': [[3.25, 1.13, 1.15],
                     [1.13, 1.36, 4.0],
                     [1.15, 4.0, 1.48]],
        'Attraction-Repulsion Strength': 4.7298,
        'Cell Ratio': [0.5, 0.5, 0.],
        'Noise Intensity': 0.28,
        'Velocity': [0.034, 0.016, 0.169],
        'Attraction-Repulsion Range': 10.2
    }
    steps = 1  # Number of steps
    # Empty list for storing global properties
    global_stats = np.zeros(N_GLOBAL_STATS * steps)
    sf = 1.  # Scale factor
    size_x = 10./sf  # Size of arena
    size_y = 10./sf  # Size of arena
    r0 = 0.1  # Core radius
    r0_x_2 = r0 * 2 # Diameter of a particle
    # Number of particles
    n = int(params["Cell Density"]*(size_x*size_y)/(2*(3**0.5)*r0*r0))
    eff_nop = float(n)  # Effective number of particles
    noise_coef=params["Noise Intensity"]
    iner_coef = params["Angular Inertia"]
    r1 = params["Attraction-Repulsion Range"]*r0
    rv = params["Alignment Range"]*r0
    f0 = params["Attraction-Repulsion Strength"]
    fa = params["Alignment Strength"]
    v0 = np.array(params["Velocity"])
    beta = np.array(params["Affinity"])
    n_per_species = np.array([n/2, n+1]).astype(np.int32)
    grad_x = np.array([np.cos(d*np.pi) * i for d, i in
                       zip(params["Gradient Angle"],
                           params["Gradient Intensity"])])
    grad_y = np.array([np.sin(d*np.pi) * i for d, i in
                       zip(params["Gradient Angle"],
                           params["Gradient Intensity"])])
    pinned = np.array([0 if x == "none" else 1 for x in
                       params["Pinned Cells"]]).astype(np.int32)
    # Particles positions and velocities
    pos_x = np.random.random(n)*size_x
    pos_y = np.random.random(n)*size_y
    dir_x = np.zeros(n)
    dir_y = np.zeros(n)

    # ---------------------C file name---------------------
    mod = ext_tools.ext_module('c_code')

    # ---------------------Main code: fixed boundary---------------------
    # Measure distance for fixed boundary condition
    fb_dist = """
    double fb_dist(double x1, double y1, double x2, double y2) {
        double r = sqrt(pow((x1-x2),2) + pow((y1-y2),2));
        return r;
    }
    """

    # Fit coordinates into the arena for fixed boundary condition
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

    # Run simulation for a give number of steps under fixed boundary
    fb_main_code = """
    int i, j, k, k2,
      start_index, end_index, start_index2, end_index2, ith_step;
    double grad_i_x, grad_i_y, align_i_x, align_i_y, f_i_x, f_i_y;
    double beta_ij, ar_slope, ar_interc, r, temp, noise, c, s, v0_i;
    double stat_align_x, stat_align_y, cm_x, cm_y, rel_pos_x, rel_pos_y;
    double stat_angular, stat_seg, stat_clu;
    int ingroup_nb, total_nb;

    for (ith_step = 0; ith_step < steps; ith_step++) {
        stat_align_x = 0;
        stat_align_y = 0;
        cm_x = 0;
        cm_y = 0;
        stat_clu = 0;

        // UPDATE DIRECTION
        start_index = 0;
        for (k = 0; k < 3; k++) {
          end_index = start_index + n_per_species[k];
          stat_seg = 0;

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
              // STAT_SEG
              ingroup_nb = 0;
              total_nb = 0;

              start_index2 = 0;
              for (k2 = 0; k2 < 3; k2++) {
                end_index2 = start_index2 + n_per_species[k2];

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
                      // STAT_SEG
                      if (k == k2) {
                        ingroup_nb += 1;
                      }
                      total_nb += 1;

                      if (r < r0_x_2) {
                        // Infinite repulsion
                        f_i_x += -10000 * (pos_x[j] - pos_x[i]);
                        f_i_y += -10000 * (pos_y[j] - pos_y[i]);
                      } else {
                        // Equilibrium attraction and repulsion
                        if (r > 0) {
                          temp = r * ar_slope + ar_interc;
                          f_i_x += temp * (pos_x[j] - pos_x[i]) / r;
                          f_i_y += temp * (pos_y[j] - pos_y[i]) / r;
                        }
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
              dir_x[i] += grad_i_x + align_i_x*fa + f_i_x;
              dir_y[i] += grad_i_y + align_i_y*fa + f_i_y;

              // NORMALIZE (ARG)
              temp = sqrt(pow(dir_x[i], 2) + pow(dir_y[i], 2));
              if (temp > 0) {
                //Avoid dividing by zero
                dir_x[i] /= temp;
                dir_y[i] /= temp;
              }

              // NOISE
              noise = noise_coef*M_PI*((static_cast <float> (rand()) /
                static_cast <float> (RAND_MAX))*2-1);
              c = cos(noise);
              s = sin(noise);
              temp = dir_x[i];
              dir_x[i] = dir_x[i]*c - dir_y[i]*s;
              dir_y[i] = temp*s + dir_y[i]*c;

              // STAT_ALIGN
              stat_align_x += dir_x[i];
              stat_align_y += dir_y[i];

              // STAT_SEG
              if (total_nb > 0) {
                stat_seg += ingroup_nb / (double) total_nb;
              }

              // STAT_CLU
              stat_clu += total_nb;
            }
          } else {
            // If cell is pinned, calculate statistics but not forces # TODO
            for (i = start_index; i < end_index; i++) {
              // STAT_SEG
              ingroup_nb = 0;
              total_nb = 0;

              start_index2 = 0;
              for (k2 = 0; k2 < 3; k2++) {
                end_index2 = start_index2 + n_per_species[k2];

                for (j = start_index2; j < end_index2; j++) {
                  if (i != j) {
                    r = fb_dist(pos_x[i], pos_y[i], pos_x[j], pos_y[j]);

                    // ATTRACTION-REPULSION
                    if (r <= r1) {
                      // STAT_SEG
                      if (k == k2) {
                        ingroup_nb += 1;
                      }
                      total_nb += 1;
                    }
                  }
                }
              start_index2 = end_index2;
              }

              // STAT_SEG
              if (total_nb > 0) {
                stat_seg += ingroup_nb / (double) total_nb;
              }

              // STAT_CLU
              stat_clu += total_nb;
            }
          }

          // SEGREGATION PARAMETER (2,3,4*steps+ith_step)
          if (n_per_species[k] > 0) {
            stat_seg /= (double) n_per_species[k] * (double) n_per_species[k];
          }
          global_stats[(2+k) * steps + ith_step] = stat_seg * n;

          start_index = end_index;
        }

        // UPDATE POSITION
        start_index = 0;
        for (k = 0; k < 3; k++) {
          end_index = start_index + n_per_species[k];

          if (pinned[k] == 0) {
            // Only if the cell type is not pinned

            // SPEED (constant across same species)
            v0_i = v0[k];

            for (i = start_index; i < end_index; i++) {
              pos_x[i] += v0_i * dir_x[i];
              pos_x[i] = fb_fitInto(pos_x[i], size_x);
              pos_y[i] += v0_i * dir_y[i];
              pos_y[i] = fb_fitInto(pos_y[i], size_y);

              //STAT_ANGULAR
              cm_x += pos_x[i];
              cm_y += pos_y[i];
            }
          }

          start_index = end_index;
        }

        // Update global stats
        if (eff_nop > 0) {
          // GROUP ANGULAR MOMENTUM (0*steps+ith_step)
          cm_x /= eff_nop;
          cm_y /= eff_nop;
          stat_angular = 0;
          for (i = 1; i < n; i++) {
            rel_pos_x = pos_x[i] - cm_x;
            rel_pos_y = pos_y[i] - cm_y;
            stat_angular += rel_pos_x * dir_y[i] - rel_pos_y * dir_x[i];
          }
          global_stats[ith_step] = abs(stat_angular) / eff_nop;

          // ORDER PARAMETER (1*steps+ith_step)
          global_stats[steps + ith_step] = sqrt(pow(stat_align_x, 2) +
            pow(stat_align_y, 2)) / eff_nop;
        }
        if (n > 0) {
          // CLUSTERING PARAMETER (5*steps+ith_step)
          global_stats[5*steps + ith_step] = (stat_clu/
            (n*M_PI*r1*r1/(size_x*size_y)))/n;
        }
    }
    """

    # ---------------------Main code: periodic boundary---------------------
    # Measure distance for periodic boundary condition
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

    # Fit coordinates into the arena for periodic boundary condition
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

    # Run simulation for a give number of steps under periodic boundary
    pb_main_code = """
    int i, j, k, k2,
      start_index, end_index, start_index2, end_index2, ith_step;
    double grad_i_x, grad_i_y, align_i_x, align_i_y, f_i_x, f_i_y;
    double beta_ij, ar_slope, ar_interc, r, temp, noise,
      c, s, v0_i, dis_x, dis_y;
    double stat_align_x, stat_align_y, cm_x, cm_y, rel_pos_x, rel_pos_y;
    double sum_c_theta_x, sum_s_theta_x, sum_c_theta_y, sum_s_theta_y;
    double stat_angular, stat_seg, stat_clu;
    int ingroup_nb, total_nb;

    for (ith_step = 0; ith_step < steps; ith_step++) {
        stat_align_x = 0;
        stat_align_y = 0;
        sum_c_theta_x = 0;
        sum_s_theta_x = 0;
        sum_c_theta_y = 0;
        sum_s_theta_y = 0;
        stat_clu = 0;

        // UPDATE DIRECTION
        start_index = 0;
        for (k = 0; k < 3; k++) {
          end_index = start_index + n_per_species[k];
          stat_seg = 0;

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
              // STAT_SEG
              ingroup_nb = 0;
              total_nb = 0;

              start_index2 = 0;
              for (k2 = 0; k2 < 3; k2++) {
                end_index2 = start_index2 + n_per_species[k2];

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
                      // STAT_SEG
                      if (k == k2) {
                        ingroup_nb += 1;
                      }
                      total_nb += 1;

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
              dir_x[i] += grad_i_x + align_i_x*fa + f_i_x;
              dir_y[i] += grad_i_y + align_i_y*fa + f_i_y;

              // NORMALIZE (ARG)
              temp = sqrt(pow(dir_x[i], 2) + pow(dir_y[i], 2));
              if (temp > 0) {
                //Avoid dividing by zero
                dir_x[i] /= temp;
                dir_y[i] /= temp;
              }

              // NOISE
              noise = noise_coef*M_PI*((static_cast <float> (rand()) /
                static_cast <float> (RAND_MAX))*2-1);
              c = cos(noise);
              s = sin(noise);
              temp = dir_x[i];
              dir_x[i] = dir_x[i]*c - dir_y[i]*s;
              dir_y[i] = temp*s + dir_y[i]*c;

              //STAT_ALIGN
              stat_align_x += dir_x[i];
              stat_align_y += dir_y[i];

              // STAT_SEG
              if (total_nb > 0) {
                stat_seg += ingroup_nb / (double) total_nb;
              }

              // STAT_CLU
              stat_clu += total_nb;
            }
          } else {
            // If cell is pinned, calculate statistics but not forces # TODO
            for (i = start_index; i < end_index; i++) {
              // STAT_SEG
              ingroup_nb = 0;
              total_nb = 0;

              start_index2 = 0;
              for (k2 = 0; k2 < 3; k2++) {
                end_index2 = start_index2 + n_per_species[k2];

                for (j = start_index2; j < end_index2; j++) {
                  if (i != j) {
                    dis_x = pb_dist(pos_x[i], pos_x[j], size_x);
                    dis_y = pb_dist(pos_y[i], pos_y[j], size_y);
                    r = sqrt(pow(dis_x,2)+pow(dis_y,2));

                    // ATTRACTION-REPULSION
                    if (r <= r1) {
                      // STAT_SEG
                      if (k == k2) {
                        ingroup_nb += 1;
                      }
                      total_nb += 1;
                    }
                  }
                }
              start_index2 = end_index2;
              }

              // STAT_SEG
              if (total_nb > 0) {
                stat_seg += ingroup_nb / (double) total_nb;
              }

              // STAT_CLU
              stat_clu += total_nb;
            }
          }

          // SEGREGATION PARAMETER (2,3,4*steps+ith_step)
          if (n_per_species[k] > 0) {
            stat_seg /= (double) n_per_species[k] * (double) n_per_species[k];
          }
          global_stats[(2+k) * steps + ith_step] = stat_seg * n;

          start_index = end_index;
        }

        // UPDATE POSITION
        start_index = 0;
        for (k = 0; k < 3; k++) {
          end_index = start_index + n_per_species[k];

          if (pinned[k] == 0) {
            // Only if the cell type is not pinned

            // SPEED (constant across same species)
            v0_i = v0[k];

            for (i = start_index; i < end_index; i++) {
              pos_x[i] += v0_i * dir_x[i];
              pos_x[i] = pb_fitInto(pos_x[i], size_x);
              pos_y[i] += v0_i * dir_y[i];
              pos_y[i] = pb_fitInto(pos_y[i], size_y);

              //STAT_ANGULAR
              temp = 2 * M_PI * pos_x[i] / size_x;
              sum_c_theta_x += cos(temp);
              sum_s_theta_x += sin(temp);

              temp = 2 * M_PI * pos_y[i] / size_y;
              sum_c_theta_y += cos(temp);
              sum_s_theta_y += sin(temp);
            }
          }

          start_index = end_index;
        }

        // Update global stats
        if (eff_nop > 0) {
          // GROUP ANGULAR MOMENTUM (0*steps+ith_step)
          sum_c_theta_x /= eff_nop;
          sum_s_theta_x /= eff_nop;
          sum_c_theta_y /= eff_nop;
          sum_s_theta_y /= eff_nop;

          cm_x = size_x * (atan2(-sum_s_theta_x, -sum_c_theta_x) + M_PI) /
            (2 * M_PI);
          cm_y = size_y * (atan2(-sum_s_theta_y, -sum_c_theta_y) + M_PI) /
            (2 * M_PI);

          stat_angular = 0;
          for (i = 1; i < n; i++) {
            rel_pos_x = pb_dist(cm_x, pos_x[i], size_x);
            rel_pos_y = pb_dist(cm_y, pos_y[i], size_y);
            stat_angular += rel_pos_x * dir_y[i] - rel_pos_y * dir_x[i];
          }
          global_stats[ith_step] = abs(stat_angular) / eff_nop;

          // ORDER PARAMETER (1*steps+ith_step)
          global_stats[steps + ith_step] = sqrt(pow(stat_align_x, 2) +
            pow(stat_align_y, 2)) / eff_nop;
        }
        if (n > 0) {
          // CLUSTERING PARAMETER (5*steps+ith_step)
          global_stats[5*steps + ith_step] = (stat_clu/(n*M_PI*r1*r1/
            (size_x*size_y)))/n;
        }
    }
    """

    # ---------------------Fixed boundary---------------------
    # Create main function from C++ code and specify input
    fb_tick_func = ext_tools.ext_function(
        'fb_tick', fb_main_code,
        ["n", "eff_nop", "size_x", "size_y", "r0_x_2", "r1", "rv", "iner_coef",
         "f0", "fa", "noise_coef", "v0", "pinned", "n_per_species", "beta",
         "grad_x", "grad_y", "pos_x", "pos_y", "dir_x", "dir_y",
         "global_stats", "steps"])
    # Add helper functions to main function
    fb_tick_func.customize.add_support_code(fb_dist)
    fb_tick_func.customize.add_support_code(fb_fit)
    fb_tick_func.customize.add_header("<math.h>")
    # Add main function to module
    mod.add_function(fb_tick_func)

    # ---------------------Periodic boundary---------------------
    # Create main function from C++ code and specify input
    pb_tick_func = ext_tools.ext_function(
        'pb_tick', pb_main_code,
        ["n", "eff_nop", "size_x", "size_y", "r0_x_2", "r1", "rv", "iner_coef",
         "f0", "fa", "noise_coef", "v0", "pinned", "n_per_species", "beta",
         "grad_x", "grad_y", "pos_x", "pos_y", "dir_x", "dir_y",
         "global_stats", "steps"])
    # Add helper functions to main function
    pb_tick_func.customize.add_support_code(pb_dist)
    pb_tick_func.customize.add_support_code(pb_fit)
    pb_tick_func.customize.add_header("<math.h>")
    # Add main function to module
    mod.add_function(pb_tick_func)
    # Compile
    mod.compile(compiler="gcc", verbose=1)

if __name__ == "__main__":
    weave_compile()
