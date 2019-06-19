// ----------------------------------------------------------------------------
// Rayleigh and Mie scattering atmosphere system
//
// implementation of the techniques described here:
// http://www.scratchapixel.com/old/lessons/3d-advanced-lessons/simulating-the-colors-of-the-sky/atmospheric-scattering/
// ----------------------------------------------------------------------------

#ifdef GL_ES
#define _in(T) const in T
#define _inout(T) inout T
#define _out(T) out T
#define _begin(type) type (
#define _end )
#define mul(a, b) (a) * (b)
#endif

#define PI 3.14159265359

// Shadertoy specific uniforms
#define u_res iResolution
#define u_time iTime
#define u_mouse iMouse

struct ray_t {
	vec3 origin;
	vec3 direction;
};
#define BIAS 1e-4 // small offset to avoid self-intersections

struct sphere_t {
	vec3 origin;
	float radius;
	int material;
};

struct plane_t {
	vec3 direction;
	float distance;
	int material;
};

mat3 rotate_around_x(_in(float) angle_degrees)
{
	float angle = radians(angle_degrees);
	float _sin = sin(angle);
	float _cos = cos(angle);
	return mat3(1, 0, 0, 0, _cos, -_sin, 0, _sin, _cos);
}


ray_t get_primary_ray(
	_in(vec3) cam_local_point,
	_inout(vec3) cam_origin,
	_inout(vec3) cam_look_at
){
	vec3 fwd = normalize(cam_look_at - cam_origin);
	vec3 up = vec3(0, 1, 0);
	vec3 right = cross(up, fwd);
	up = cross(fwd, right);

	ray_t r = _begin(ray_t)
		cam_origin,
		normalize(fwd + up * cam_local_point.y + right * cam_local_point.x)
		_end;
	return r;
}

bool isect_sphere(_in(ray_t) ray, _in(sphere_t) sphere, _inout(float) t0, _inout(float) t1)
{
	vec3 rc = sphere.origin - ray.origin;
	float radius2 = sphere.radius * sphere.radius;
	float tca = dot(rc, ray.direction);
	float d2 = dot(rc, rc) - tca * tca;
	if (d2 > radius2) return false;
	float thc = sqrt(radius2 - d2);
	t0 = tca - thc;
	t1 = tca + thc;

	return true;
}

// scattering coefficients at sea level (m)
const vec3 betaR = vec3(5.5e-6, 13.0e-6, 22.4e-6); // Rayleigh
const vec3 betaM = vec3(21e-6); // Mie

// scale height (m)
// thickness of the atmosphere if its density were uniform
const float hR = 7994.0; // Rayleigh
const float hM = 1200.0; // Mie

float rayleigh_phase_func(float mu)
{
	return
			3. * (1. + mu*mu)
	/ //------------------------
				(16. * PI);
}

// Henyey-Greenstein phase function factor [-1, 1]
// represents the average cosine of the scattered directions
// 0 is isotropic scattering
// > 1 is forward scattering, < 1 is backwards
const float g = 0.76;
float henyey_greenstein_phase_func(float mu)
{
	return
						(1. - g*g)
	/ //---------------------------------------------
		((4. + PI) * pow(1. + g*g - 2.*g*mu, 1.5));
}

// Schlick Phase Function factor
// Pharr and  Humphreys [2004] equivalence to g above
const float k = 1.55*g - 0.55 * (g*g*g);
float schlick_phase_func(float mu)
{
	return
					(1. - k*k)
	/ //-------------------------------------------
		(4. * PI * (1. + k*mu) * (1. + k*mu));
}

const float earth_radius = 6360e3; // (m)
const float atmosphere_radius = 6420e3; // (m)

vec3 sun_dir = vec3(0, 1, 0);
const float sun_power = 20.0;

const sphere_t atmosphere = _begin(sphere_t)
	vec3(0, 0, 0), atmosphere_radius, 0
_end;

const int num_samples = 16;
const int num_samples_light = 8;

float approx_air_column_density_ratio_along_2d_ray_for_curved_world(
    float x_start, // distance along path from closest approach at which we start the raymarch
    float x_stop,  // distance along path from closest approach at which we stop the raymarch
    float z2,      // distance at closest approach, squared
    float r,       // radius of the planet
    float H        // scale height of the planet's atmosphere
){

    // GUIDE TO VARIABLE NAMES:
    //  "x*" distance along the ray from closest approach
    //  "z*" distance from the center of the world at closest approach
    //  "r*" distance ("radius") from the center of the world
    //  "h*" distance ("height") from the surface of the world
    //  "*b" variable at which the slope and intercept of the height approximation is sampled
    //  "*0" variable at which the surface of the world occurs
    //  "*1" variable at which the top of the atmosphere occurs
    //  "*2" the square of a variable
    //  "d*dx" a derivative, a rate of change over distance along the ray

    float a = 0.45;
    float b = 0.45;

    float x0 = sqrt(max(r *r -z2, 0.));
    // if ray is obstructed
    if (x_start < x0 && -x0 < x_stop && z2 < r*r)
    {
        // return ludicrously big number to represent obstruction
        return 1e20;
    }

    float r1      = r + 6.*H;
    float x1      = sqrt(max(r1*r1-z2, 0.));
    float xb      = x0+(x1-x0)*b;
    float rb2     = xb*xb + z2;
    float rb      = sqrt(rb2);
    float d2hdx2  = z2 / sqrt(rb2*rb2*rb2);
    float dhdx    = xb / rb;
    float hb      = rb - r;
    float dx0     = x0          -xb;
    float dx_stop = abs(x_stop )-xb;
    float dx_start= abs(x_start)-xb;
    float h0      = (0.5 * a * d2hdx2 * dx0      + dhdx) * dx0      + hb;
    float h_stop  = (0.5 * a * d2hdx2 * dx_stop  + dhdx) * dx_stop  + hb;
    float h_start = (0.5 * a * d2hdx2 * dx_start + dhdx) * dx_start + hb;

    float rho0  = exp(-h0/H);
    float sigma =
        sign(x_stop ) * max(H/dhdx * (rho0 - exp(-h_stop /H)), 0.)
      - sign(x_start) * max(H/dhdx * (rho0 - exp(-h_start/H)), 0.);

    // NOTE: we clamp the result to prevent the generation of inifinities and nans,
    // which can cause graphical artifacts.
    return min(abs(sigma),1e20);
}

// "approx_air_column_density_ratio_along_3d_ray_for_curved_world" is just a convenience wrapper
//   for the above function that works with 3d vectors.
float approx_air_column_density_ratio_along_3d_ray_for_curved_world (
    vec3  P, // position of viewer
    vec3  V, // direction of viewer (unit vector)
    float x, // distance from the viewer at which we stop the "raymarch"
    float r, // radius of the planet
    float H  // scale height of the planet's atmosphere
){
    float xz = dot(-P,V);           // distance ("radius") from the ray to the center of the world at closest approach, squared
    float z2 = dot( P,P) - xz * xz; // distance from the origin at which closest approach occurs
    return approx_air_column_density_ratio_along_2d_ray_for_curved_world( 0.-xz, x-xz, z2, r, H );
}

bool get_sun_light(
	_in(ray_t) ray,
	_inout(float) optical_depthR,
	_inout(float) optical_depthM
){
	float t0, t1;
	isect_sphere(ray, atmosphere, t0, t1);

    // // this is the implementation using classical raymarching
	// float march_pos = 0.;
	// float march_step = t1 / float(num_samples_light);
    //
	// for (int i = 0; i < num_samples_light; i++) {
	// 	vec3 s =
	// 		ray.origin +
	// 		ray.direction * (march_pos + 0.5 * march_step);
	// 	float height = length(s) - earth_radius;
	// 	if (height < 0.)
	// 		return false;
    //
	// 	optical_depthR += exp(-height / hR) * march_step;
	// 	optical_depthM += exp(-height / hM) * march_step;
    //
	// 	march_pos += march_step;
	// }

    // this is the implementation using a fast closed form approximation
    optical_depthR =
        approx_air_column_density_ratio_along_3d_ray_for_curved_world (
            ray.origin,    // position of viewer
            ray.direction, // direction of viewer (unit vector)
            t1, // distance from the viewer at which we stop the "raymarch"
            earth_radius, // radius of the planet
            hR  // scale height of the planet's atmosphere
        );
    optical_depthM =
        approx_air_column_density_ratio_along_3d_ray_for_curved_world (
            ray.origin,    // position of viewer
            ray.direction, // direction of viewer (unit vector)
            t1, // distance from the viewer at which we stop the "raymarch"
            earth_radius, // radius of the planet
            hM  // scale height of the planet's atmosphere
        );

	return true;
}
vec3 get_incident_light(_in(ray_t) ray)
{
	// "pierce" the atmosphere with the viewing ray
	float t0, t1;
	if (!isect_sphere(
		ray, atmosphere, t0, t1)) {
		return vec3(0);
	}

	float march_step = t1 / float(num_samples);

	// cosine of angle between view and light directions
	float mu = dot(ray.direction, sun_dir);

	// Rayleigh and Mie phase functions
	// A black box indicating how light is interacting with the material
	// Similar to BRDF except
	// * it usually considers a single angle
	//   (the phase angle between 2 directions)
	// * integrates to 1 over the entire sphere of directions
	float phaseR = rayleigh_phase_func(mu);
	float phaseM =
#if 1
		henyey_greenstein_phase_func(mu);
#else
		schlick_phase_func(mu);
#endif

	// optical depth (or "average density")
	// represents the accumulated extinction coefficients
	// along the path, multiplied by the length of that path
	float optical_depthR = 0.;
	float optical_depthM = 0.;

	vec3 sumR = vec3(0);
	vec3 sumM = vec3(0);
	float march_pos = 0.;

	for (int i = 0; i < num_samples; i++) {
		vec3 s =
			ray.origin +
			ray.direction * (march_pos + 0.5 * march_step);
		float height = length(s) - earth_radius;

		// integrate the height scale
		float hr = exp(-height / hR) * march_step;
		float hm = exp(-height / hM) * march_step;
		optical_depthR += hr;
		optical_depthM += hm;

		// gather the sunlight
		ray_t light_ray = _begin(ray_t)
			s,
			sun_dir
		_end;
		float optical_depth_lightR = 0.;
		float optical_depth_lightM = 0.;
		bool overground = get_sun_light(
			light_ray,
			optical_depth_lightR,
			optical_depth_lightM);

		if (overground) {
			vec3 tau =
				betaR * (optical_depthR + optical_depth_lightR) +
				betaM * 1.1 * (optical_depthM + optical_depth_lightM);
			vec3 attenuation = exp(-tau);

			sumR += hr * attenuation;
			sumM += hm * attenuation;
		}

		march_pos += march_step;
	}

	return
		sun_power *
		(sumR * phaseR * betaR +
		sumM * phaseM * betaM);
}

void mainImage(_out(vec4) fragColor, vec2 fragCoord)
{
	vec2 aspect_ratio = vec2(u_res.x / u_res.y, 1);
	float fov = tan(radians(45.0));
	vec2 point_ndc = fragCoord.xy / u_res.xy;
	vec3 point_cam = vec3((2.0 * point_ndc - 1.0) * aspect_ratio * fov, -1.0);

	vec3 col = vec3(0);

	// sun
	mat3 rot = rotate_around_x(-abs(sin(u_time / 2.)) * 90.);
	sun_dir *= rot;

    if (u_mouse.z < 0.1) {
        // sky dome angles
        vec3 p = point_cam;
        float z2 = p.x * p.x + p.y * p.y;
        float phi = atan(p.y, p.x);
        float theta = acos(1.0 - z2);
        vec3 dir = vec3(
            sin(theta) * cos(phi),
            cos(theta),
            sin(theta) * sin(phi));

        ray_t ray = _begin(ray_t)
            vec3(0, earth_radius + 1., 0),
            dir
        _end;

        col = get_incident_light(ray);
    } else {
        vec3 eye = vec3 (0, earth_radius + 1., 0);
        vec3 look_at = vec3 (0, earth_radius + 1.5, -1);

        ray_t ray = get_primary_ray(point_cam, eye, look_at);

        if (dot(ray.direction, vec3(0, 1, 0)) > .0) {
            col = get_incident_light(ray);
        } else {
            col = vec3 (0.333);
        }
    }

	fragColor = vec4(col, 1);
}
