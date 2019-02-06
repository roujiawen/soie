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
    n = int(params["Cell Density"]*(size_x*size_y)/(2*(3**0.5)*r0*r0))
    nint=params["Noise Intensity"]
    inert = params["Angular Inertia"]
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

    v_x = np.zeros(n)
    v_y = np.zeros(n)

    #---------------------C file name---------------------
    mod = ext_tools.ext_module('c_code')

    #---------------------Main code---------------------
    get_cell_type = """
    int cellType(int cellId, int* cutoff) {
        if (cellId > cutoff[1]) {
            return 2;
        } else if (cellId < cutoff[0]) {
            return 0;
        } else {
            return 1;
        }
    }
    """

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
    int i;
    int j;
    int ctype;
    double r;
    double temp;
    double noise;
    double c;
    double s;
    double f_x;
    double f_y;
    double avgdir_x;
    double avgdir_y;
    int inf_count;

    for (i = 0; i < n; i++)
    {
        ctype = cellType(i, cutoff);
        if (pinned[ctype] == 0) {
            // Initiate Attraction-Repulsion Strengths
            f_x = 0;
            f_y = 0;
            inf_count = 0;
            // Initiate Alignment Strengths
            avgdir_x = 0;
            avgdir_y = 0;

            for (j = 0; j < n; j++)
            {
                r = fb_dist(pos_x[i], pos_y[i], pos_x[j], pos_y[j]);
                //Attraction-Repulsion Strength
                if (i != j) {
                    if (r <= r1) {
                        if (r < r0) {
                            //Infinite repulsion
                            if (inf_count == 0) {
                                f_x = 0;
                                f_y = 0;
                            }
                            inf_count++;
                            if (r > 0) {//Avoid dividing by zero
                                f_x += (pos_x[i]-pos_x[j])/r;
                                f_y += (pos_y[i]-pos_y[j])/r;
                            }
                        } else {
                            //Equilibrium attraction and repulsion
                            if (inf_count == 0){
                                temp = -f0 + (r-r0)/(r1-r0)*(1+beta[ctype*3+cellType(j, cutoff)])*f0;
                                f_x += temp*(pos_x[j]-pos_x[i])/r;
                                f_y += temp*(pos_y[j]-pos_y[i])/r;
                            }
                        }
                    }
                }
                //Alignment Strength
                if (r <= rv) {
                    temp = sqrt(pow(v_x[j],2) + pow(v_y[j],2));
                    if (temp > 0) {
                        avgdir_x += v_x[j]/temp;
                        avgdir_y += v_y[j]/temp;
                    }
                }
            }

            // ANGULAR INERTIA
            v_x[i] *= inert;
            v_y[i] *= inert;

            // INTERACTION
            if (inf_count > 0) {
                f_x = f_x/inf_count*10000;
                f_y = f_y/inf_count*10000;
            }
            v_x[i] += f_x;
            v_y[i] += f_y;

            // ALIGNMENT
            temp = sqrt(pow(avgdir_x,2) + pow(avgdir_y,2));
            if (temp > 0) {//Avoid dividing by zero
                avgdir_x /= temp;
                avgdir_y /= temp;
            }
            v_x[i] += fa * avgdir_x;
            v_y[i] += fa * avgdir_y;

            //GRADIENT
            v_x[i] += grad_x[ctype];
            v_y[i] += grad_y[ctype];

            //NORMALIZE into unit vector (contain angle info)
            temp = sqrt(pow(v_x[i],2) + pow(v_y[i],2));
            if (temp > 0) {//Avoid dividing by zero
                v_x[i] /= temp;
                v_y[i] /= temp;
            }

            //NOISE
            noise = nint*M_PI*((static_cast <float> (rand()) / static_cast <float> (RAND_MAX))*2-1);
            c = cos(noise);
            s = sin(noise);
            temp = v_x[i];
            v_x[i] = v0[ctype]*(v_x[i]*c - v_y[i]*s);
            v_y[i] = v0[ctype]*(temp*s + v_y[i]*c);
        }
    }

    for (i = 0; i < n; i++)
    {
        ctype = cellType(i, cutoff);
        if (pinned[ctype] == 0) {
            //WITHIN BOUNDARY
            pos_x[i] += v_x[i];
            pos_x[i] = fb_fitInto(pos_x[i], size_x);
            pos_y[i] += v_y[i];
            pos_y[i] = fb_fitInto(pos_y[i], size_y);
        }
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
    int i;
    int j;
    int ctype;
    double r;
    double temp;
    double noise;
    double c;
    double s;
    double f_x;
    double f_y;
    double dis_x;
    double dis_y;
    double avgdir_x;
    double avgdir_y;
    int inf_count;

    for (i = 0; i < n; i++)
    {
        ctype = cellType(i, cutoff);
        if (pinned[ctype] == 0) {
            // Initiate Attraction-Repulsion Strengths
            f_x = 0;
            f_y = 0;
            inf_count = 0;
            // Initiate Alignment Strengths
            avgdir_x = 0;
            avgdir_y = 0;

            for (j = 0; j < n; j++)
            {
                dis_x = pb_dist(pos_x[i], pos_x[j], size_x);
                dis_y = pb_dist(pos_y[i], pos_y[j], size_y);
                r = sqrt(pow(dis_x,2)+pow(dis_y,2));
                //Attraction-Repulsion Strength
                if (i != j) {
                    if (r <= r1) {
                        if (r < r0) {
                            //Infinite repulsion
                            if (inf_count == 0) {
                                f_x = 0;
                                f_y = 0;
                            }
                            inf_count++;
                            if (r > 0) {//Avoid dividing by zero
                                f_x += -dis_x/r;
                                f_y += -dis_y/r;
                            }
                        } else {
                            //Equilibrium attraction and repulsion
                            if (inf_count == 0){
                                temp = -f0 + (r-r0)/(r1-r0)*(1.+beta[ctype*3+cellType(j, cutoff)])*f0;
                                f_x += temp*(dis_x)/r;
                                f_y += temp*(dis_y)/r;
                            }
                        }
                    }
                }
                //Alignment Strength
                if (r <= rv) {
                    temp = sqrt(pow(v_x[j],2) + pow(v_y[j],2));
                    if (temp > 0) {
                        avgdir_x += v_x[j]/temp;
                        avgdir_y += v_y[j]/temp;
                    }
                }
            }

            // ANGULAR INERTIA
            v_x[i] *= inert;
            v_y[i] *= inert;

            // INTERACTION
            if (inf_count > 0) {
                f_x = f_x/inf_count*10000;
                f_y = f_y/inf_count*10000;
            }
            v_x[i] += f_x;
            v_y[i] += f_y;

            // ALIGNMENT
            temp = sqrt(pow(avgdir_x,2) + pow(avgdir_y,2));
            if (temp > 0) {//Avoid dividing by zero
                avgdir_x /= temp;
                avgdir_y /= temp;
            }
            v_x[i] += fa * avgdir_x;
            v_y[i] += fa * avgdir_y;

            //GRADIENT
            v_x[i] += grad_x[ctype];
            v_y[i] += grad_y[ctype];

            //NORMALIZE into unit vector (contain angle info)
            temp = sqrt(pow(v_x[i],2) + pow(v_y[i],2));
            if (temp > 0) {//Avoid dividing by zero
                v_x[i] /= temp;
                v_y[i] /= temp;
            }

            //NOISE
            noise = nint*M_PI*((static_cast <float> (rand()) / static_cast <float> (RAND_MAX))*2-1);
            c = cos(noise);
            s = sin(noise);
            temp = v_x[i];
            v_x[i] = v0[ctype]*(v_x[i]*c - v_y[i]*s);
            v_y[i] = v0[ctype]*(temp*s + v_y[i]*c);
        }
    }

    for (i = 0; i < n; i++)
    {
        ctype = cellType(i, cutoff);
        if (pinned[ctype] == 0) {
            //WITHIN BOUNDARY
            pos_x[i] += v_x[i];
            pos_x[i] = pb_fitInto(pos_x[i], size_x);
            pos_y[i] += v_y[i];
            pos_y[i] = pb_fitInto(pos_y[i], size_y);
        }
    }



    """

    fb_tick_func = ext_tools.ext_function('fb_tick',fb_main_code,
                    ["n","size_x", "size_y","r0","r1","rv","inert",
                     "f0","fa", "nint", "v0", "pinned",
                     "cutoff", "beta", "grad_x", "grad_y",
                     "pos_x","pos_y","v_x","v_y"])
    fb_tick_func.customize.add_support_code(get_cell_type)
    fb_tick_func.customize.add_support_code(fb_dist)
    fb_tick_func.customize.add_support_code(fb_fit)
    fb_tick_func.customize.add_header("<math.h>")
    mod.add_function(fb_tick_func)


    pb_tick_func = ext_tools.ext_function('pb_tick',pb_main_code,
                    ["n","size_x", "size_y","r0","r1","rv","inert",
                     "f0","fa", "nint", "v0", "pinned",
                     "cutoff", "beta", "grad_x", "grad_y",
                     "pos_x","pos_y","v_x","v_y"])
    pb_tick_func.customize.add_support_code(get_cell_type)
    pb_tick_func.customize.add_support_code(pb_dist)
    pb_tick_func.customize.add_support_code(pb_fit)
    pb_tick_func.customize.add_header("<math.h>")
    mod.add_function(pb_tick_func)

    mod.compile(compiler="gcc", verbose=0)

if __name__ == "__main__":
    weave_compile()
