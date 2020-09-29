
#ifndef _ED_ATTRACTOR_H

/* strange attractor versions
all functions return velocity at a point on attractor

THANK YOU 3d-meier.de
*/

vector lorentzAttractor(vector p;
    float a, b, c){
        // a is "disk size" : 12
        // b is "disk separation" : 26
        // c is "band thickness" : 6
        return set(
            a * (p.y - p.x), //x
            p.x * (b - p.z) - p.y, //y
            p.x * p.y - c * p.z ); //z
    }

vector rosslerAttractor(vector p;
    float a, b, c){
        // more sensitive
        return set(
            - (p.y + p.z),
            p.x + a * p.y,
            b + p.z * (p.x - c)
        );
    }

vector centredRosslerAttractor(vector p;
    float a, b, c, d){
        /* modification to centre "chair back" of normal Rossler
        original has projection in +x -y
        a : 0.191
        b : 0.892
        c : 10
        d "centre force" : 4
        close enough, the imbalance isn't nearly as pronounced
        and it's not in the nature of these things to be symmetrical
        */
        return set(
            - (p.y + p.z) ,
            d * p.x + a * p.y,
            b + p.z * ((p.x) - c)
        );
    }

float chuaComponent(float x, d, e){
    return e * x + (d + e) * (abs(x + 1) - abs(x-1));
}

vector chuaAttractor(vector p;
    float a, b, c, d, e){
        /* two full parallel-ish orbits
        a : 20.9
        b : 21
        c : 20.6
        d : -1
        e : -0.5
        */
        return set(
            a * (p.y - p.x - chuaComponent(p.x, d, e)),
            b * (p.x - p.y + p.z),
            -c * p.y
        );
    }

vector henonAttractor(vector p;
    float a, b){
        // sucks
        return set(
            1 + p.y - pow(a * p.x, 2),
            //1 + p.y - a * pow(p.x, 2),
            b * p.x,
            0
        );
    }

vector metzlerAttractor(vector p; // do not advect
    float a){
        return set(
            p.x + a * ( p.x - pow(p.x, 2) + p.y),
            p.y + a * ( p.y - pow(p.y, 2) + p.x),
            0
        );
        /* tried to give this volume, but static nature makes it impossible
        to find inner structure, ends up as tube or sphere
        */
    }

vector ikedaAttractor( vector p; // do not advect
    float a, b, c, d){
        // swirly spiral
        float t = c - d / (1 + p.x * p.x + p.y * p.y);
        return set(
            a + b * (p.x * cos(t) - p.y * sin(t)),
            b * (p.x * sin(t) + p.y * cos(t)),
            0.0
        );
    }

vector cockatooAttractor( vector p; // do not advect
    float a, b, c){
        // only attracts points, very cool
        return set(
            p.y * (1 + sin(a * p.x)) - b * sqrt(abs(p.x)),
            c - p.x,
            0.0
        );
    }

vector kanekoIAttractor( vector p;
    float a, b){
        return set(
            a * p.x + (1 - a) * ( 1 - b * pow(p.y, 2)),
            p.x,
            0
        );
    } // works like cross section along b axis

#define _ED_ATTRACTOR_H
#endif
