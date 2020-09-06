

///// XAPKOHHEH's polygon raytracer

float shaderay(vector sp;vector ld){
    if(!chi("shadows"))return 1.0;

    float bias=0.0001;
    vector cp;
    vector cpruv;
    int cpr=intersect(1,sp+normalize(ld)*bias,ld,cp,cpruv);
    if(cpr==-1)return 1.0;

    int mat=primuv(1,"mat",cpr,cpruv);
    if(mat==2)return 1.0;
    else return 0.0;
}

float calc_ambocc(vector sp;vector sn;float dist){
    if(!chi("ambocc"))return 1.0;
    int samples=chi("amboccsamples");
    float bias=0.0001;
    float occ=0;
    for(int i=0;i<samples;++i){
        vector ray=normalize(rand(sp+2.314+i*4.9318)-set(0.5,0.5,0.5));
        if(dot(ray,sn)<0)ray*=-1.0;
        vector cp,cpruv;
        int cpr=intersect(1,sp+bias*ray,ray*dist,cp,cpruv);
        if(cpr==-1){
            occ+=1;
            continue;
        }
        occ+=length((sp-cp)/dist);
    }
    occ/=samples;
    return occ;
}

vector calc_phong(vector cp;vector cn;vector v_v){

    int nlights=npoints(2);
    vector diff={0,0,0};
    int lsamples=min(chi("lightsamples"),nlights);
    int atten=chi("lightpcatten");
    float intmult=ch("lightintmult");
    for(int i=0;i<lsamples;++i){
        int sampt=(i*(nlights/lsamples)+int(rand(cp*2.3412)*nlights))%nlights;
        vector lp=point(2,"P",sampt);
        float intensity=point(2,"intensity",sampt)/float(lsamples) * intmult;
        vector lcd=point(2,"Cd",sampt);

        vector lray=lp-cp;
        if(atten){
            intensity*=1/length2(lray);
        }

        float shade=shaderay(cp,lray);
        float occ=calc_ambocc(cp,cn,1);

        lray=normalize(lray);
        vector lrayr=reflect(-lray,cn);
        diff+=lcd*intensity*max(shade*occ*(dot(cn,lray) + 2*pow(max(dot(normalize(v_v),lrayr),0),8)),0);
    }
    return diff;
}


vector castaray(vector p_c;vector dir_c;int maxdepth_c){
    vector p=p_c;
    vector dir=dir_c;
    vector envclr=set(0,0,0);
    vector cp,cpruv;
    vector cn;
    vector resclr=set(0,0,0); //this is the result color
    float reflblendcoeff=1; //this is something like the ray intensity - used here to do reflections without recursion
    for(int depth=0;depth<maxdepth_c;++depth){

        int cpr=intersect(1,p+normalize(dir)*0.001,dir,cp,cpruv);
        if(cpr==-1){ //ray hits infinity, sample env
            string texname=detail(3,"texname",0);
            cpr=intersect(3,p+normalize(dir)*0.001,2*dir,cp,cpruv);
            if(cpr==-1)return resclr+reflblendcoeff*envclr;   //somehow
            vector uv=primuv(3,"uv",cpr,cpruv);
            envclr=texture(texname,uv.x,uv.y);
            return resclr+reflblendcoeff*envclr;
        }
        vector cclr=primuv(1,"Cd",cpr,cpruv);

        int nlights=npoints(2);
        if(nlights==0){
            return cclr;
        }

        cn=normalize(primuv(1,"N",cpr,cpruv));
        if(dot(cn,dir)>0)cn*=-1;    //like 2-sided surfaces
        int mat=primuv(1,"mat",cpr,cpruv);

        //here we switch between 5 known materials per polygon
        //a lot of parameters are hardcoded because of laziness, but they can easily be
        //sampled from the surface material too
        if(mat==0){ //phong
            vector diff=calc_phong(cp,cn,-dir);
            resclr+=reflblendcoeff*cclr*diff;
            break;
        }else
        if(mat==1){//reflect
            p=cp;
            float refl=primuv(1,"reflectivity",cpr,cpruv);
            if(refl<1.0){
                resclr+=reflblendcoeff*(1-refl)*calc_phong(cp,cn,-dir);
                reflblendcoeff*=refl;
            }
            dir=reflect(dir,cn);
            continue;
            //because vex does not allow recursion, and actually all these funcs are inline code
            // we have to either fully imitate recursion stack urselves
            // or do a little trick like this here
            // part of nonreflected part of material is sampled as opaque material (phong, textures etc)
            // and mixed to resclr with (1-refl) coeff
            // but global ray "intensity" like (reflblendcoeff) is multiplied with refl (becomes dimmer for further iterations)
            // so this way we get away without stack, but we cannot spawn rays of the same nature
        }else
        if(mat==2){//constant
            resclr+=reflblendcoeff*cclr;
            break;
        }else
        if(mat==3){ //brdf-like
            p=cp;
            float refl=primuv(1,"reflectivity",cpr,cpruv);
            refl*=pow(1-abs(dot(normalize(-dir),cn)),2);
            if(refl<1.0){
                resclr+=reflblendcoeff*(1-refl)*calc_phong(cp,cn,-dir);
                reflblendcoeff*=refl;
            }
            dir=reflect(dir,cn);
            continue;
        }else
        if(mat==4){ //brdf-like with texture!
            p=cp;
            float refl=primuv(1,"reflectivity",cpr,cpruv);

            vector uv=primuv(1,"uv",cpr,cpruv);
            vector tex_nsample=texture(prim(1,"texture_norm",cpr),uv.x,uv.y,"srccolorspace","linear");
            vector tex_dsample=texture(prim(1,"texture_diff",cpr),uv.x,uv.y,"srccolorspace","linear");
            vector tex_hsample=texture(prim(1,"texture_heig",cpr),uv.x,uv.y,"srccolorspace","linear");
            float ht=1.0;
            matrix3 tang=primuv(1,"tt",cpr,cpruv);
            vector geon=cn;
            if(length2(tex_nsample)!=0)
                cn=normalize(lerp(cn,normalize((tex_nsample-set(0.5,0.5,0.5))*tang),ht));

            refl*=pow(1-abs(dot(normalize(-dir),cn)),4);

            if(refl<1.0){
                resclr+=reflblendcoeff*(1-refl)*calc_phong(cp,cn,-dir)*tex_dsample;
                reflblendcoeff*=refl;
            }
            dir=reflect(dir,cn);
            p+=geon*0.025*ht*tex_hsample;
            continue;
        }

    }
    return resclr;
}


// IT ALL STARTS HERE
float pixsize=0;
{
    int pt1=primpoint(0,@primnum,0);
    int pt2=primpoint(0,@primnum,1);
    vector p1=point(0,"P",pt1);
    vector p2=point(0,"P",pt2);
    pixsize=length(p1-p2);
}// we calc size of the grid polygon ("pixel") to do multisampling

vector bbmax,bbmin;
getbbox(0,bbmin,bbmax);
vector center=(bbmin+bbmax)*0.5; //it's kinda half-assed but i forgot to do proper camera movement)
// if u want - just precalc the grid center in detail attrib and get it here
vector n=v@N;//detail(0,"N",0);
vector fovoffset=n*ch("fov");//// see, fov is not quite fov )
vector orig=center+fovoffset;
vector aperture[];
float eyesize=ch("apsize");
int appoints=chi("apertsamples");
if(chi("dodof")){
    for(int i=0;i<appoints;++i){
        vector side=normalize(cross(set(0,1,0),n));
        push(aperture,rand(i*1.23)*eyesize*qrotate(quaternion(radians(360/appoints*i),n),side));
        //so actually we shouldnt just pick samples in the corners of the aperture mask,
        //but make a set of samples inside the surface of aperture
        // it's easy, so it's for u to implement
    }
}else push(aperture,set(0,0,0));

vector clr={0,0,0};
int samplecount=chi("multisampl");
float dofpoint=ch("focaldist");
int maxdepth=chi("maxdepth");
for(int apsmp=0;apsmp<len(aperture);++apsmp){ //so for each aperture sample
    for(int sample=0;sample<samplecount*samplecount;++sample){ //and for each pixel multisample
        //we calc offset to pixel center
        vector offset=pixsize*(set(0,sample%samplecount+0.5,sample/samplecount+0.5)/samplecount-set(0.5,0.5,0.5));//gird of samplecount side per each pixel
        offset=offset-n*dot(n,offset);
        vector p=@P+(sample!=0)*offset+aperture[apsmp];//this way we make aperture rays focus in focal distance
        vector ray=normalize(p-orig)*dofpoint-aperture[apsmp]; //this way we imitate rays coming from an aperture instead of a pixel
        clr+=castaray(p,ray*100,maxdepth);
    }
}
clr/=samplecount*samplecount*len(aperture);// and we just average all samples' colors
v@Cd=clr;





////////////////////////////
///// below is another by one whose name I have shamefully lost
////////////////////////////


#define MAX_BOUNCES 8
#define NEAR_DISTANCE 1.0e-3
#define FAR_DISTANCE 1.0e3

#define MATERIAL_LAMBERT 0
#define MATERIAL_METAL 1
#define MATERIAL_DIELECTRIC 2

#define GEOS_INPUT_IDX 1

#define SKY_RAMP_NAME "sky"

#define ALBEDO_ATTRIB_NAME "Cd"
#define NORMAL_ATTRIB_NAME "N"
#define MATERIAL_ATTRIB_NAME "material"
#define FUZZINESS_ATTRIB_NAME "fuzziness"
#define IOR_ATTRIB_NAME "ior"

struct Ray {
    vector origin;
    vector direction;
};

struct Hit {
    int prim;
    vector uvw;
    vector pos;
    vector normal;
};

void
trace(export int hitten; export Hit hit; const Ray ray)
{
    vector pos;
    vector uvw;
    int prim;

    prim = intersect(
        GEOS_INPUT_IDX,
        ray.origin
            + ray.direction * {NEAR_DISTANCE, NEAR_DISTANCE, NEAR_DISTANCE},
        ray.direction * {FAR_DISTANCE, FAR_DISTANCE, FAR_DISTANCE},
        pos,
        uvw);
    hitten = prim > -1;
    if (hitten) {
        hit.prim = prim;
        hit.uvw = uvw;
        hit.pos = pos;
        hit.normal = primuv(
            GEOS_INPUT_IDX, NORMAL_ATTRIB_NAME, hit.prim, hit.uvw);
    }
}

void
evalLambertianMaterial(export int scattered;
                       export Ray scatteredRay;
                       export vector attenuation;
                       const Ray ray;
                       const Hit hit)
{
    vector randomPos;
    vector target;

    randomPos = sample_sphere_uniform(set(nrandom(), nrandom(), nrandom()));
    target = hit.pos + hit.normal + randomPos;

    attenuation = primuv(GEOS_INPUT_IDX, ALBEDO_ATTRIB_NAME, hit.prim, hit.uvw);
    scatteredRay = Ray(hit.pos, normalize(target - hit.pos));
    scattered = 1;
}

void
evalMetallicMaterial(export int scattered;
                     export Ray scatteredRay;
                     export vector attenuation;
                     const Ray ray;
                     const Hit hit)
{
    vector randomPos;
    float fuzziness;

    randomPos = sample_sphere_uniform(set(nrandom(), nrandom(), nrandom()));
    fuzziness = min(
        primuv(GEOS_INPUT_IDX, FUZZINESS_ATTRIB_NAME, hit.prim, hit.uvw), 1.0);

    attenuation = primuv(GEOS_INPUT_IDX, ALBEDO_ATTRIB_NAME, hit.prim, hit.uvw);
    scatteredRay = Ray(
        hit.pos, reflect(ray.direction, hit.normal) + randomPos * fuzziness);
    scattered = dot(scatteredRay.direction, hit.normal) > 0;
}

void
evalDielectricMaterial(export int scattered;
                       export Ray scatteredRay;
                       export vector attenuation;
                       const Ray ray;
                       const Hit hit)
{
    float iDotN;
    float ior;
    float iorRatio;
    vector outNormal;
    float cosine;
    float reflectedAmount;
    float refractedAmount;

    attenuation = {1.0, 1.0, 1.0};
    scattered = 1;

    iDotN = dot(ray.direction, hit.normal);
    ior = ior = primuv(GEOS_INPUT_IDX, IOR_ATTRIB_NAME, hit.prim, hit.uvw);

    if (iDotN < 0) {
        // The ray comes from outside the surface.
        iorRatio = 1.0 / ior;
        outNormal = hit.normal;
        cosine = -iDotN / length(ray.direction);
    } else {
        // The ray comes from inside the surface.
        iorRatio = ior;
        outNormal = -hit.normal;
        cosine = ior * iDotN / length(ray.direction);
    }

    fresnel(
        ray.direction, outNormal, iorRatio, reflectedAmount, refractedAmount);
    if (nrandom() < reflectedAmount) {
        scatteredRay = Ray(hit.pos, reflect(ray.direction, hit.normal));
        return;
    }

    scatteredRay = Ray(hit.pos, refract(ray.direction, outNormal, iorRatio));
}

void
getColor(export vector color; const Ray ray)
{
    int i;
    Ray stack[];
    vector accumulator[];
    int hitten;
    Hit hit;

    i = 0;
    push(stack, ray);
    while (len(stack) > 0) {
        Ray currentRay;

        currentRay = pop(stack);
        trace(hitten, hit, currentRay);
        if (hitten && i < MAX_BOUNCES) {
            int material;
            int scattered;
            Ray scatteredRay;
            vector attenuation;

            material = prim(GEOS_INPUT_IDX, MATERIAL_ATTRIB_NAME, hit.prim);
            if (material == MATERIAL_LAMBERT) {
                evalLambertianMaterial(
                    scattered, scatteredRay, attenuation, currentRay, hit);
            } else if (material == MATERIAL_METAL) {
                evalMetallicMaterial(
                    scattered, scatteredRay, attenuation, currentRay, hit);
            } else if (material == MATERIAL_DIELECTRIC) {
                evalDielectricMaterial(
                    scattered, scatteredRay, attenuation, currentRay, hit);
            } else {
                warning("unsupported material");
                push(accumulator, {1.0, 0.078, 0.576});
                break;
            }

            if (scattered) {
                push(accumulator, attenuation);
                push(stack, scatteredRay);
            } else {
                push(accumulator, {0.0, 0.0, 0.0});
            }

            ++i;
        } else {
            float v;

            v = dot(normalize(set(
                        currentRay.direction.x, 0.0, currentRay.direction.z)),
                    currentRay.direction);
            v = currentRay.direction.y < 0 ? 0.0 : 1.0 - v;
            push(accumulator, chramp(SKY_RAMP_NAME, v));
        }
    }

    color = {1.0, 1.0, 1.0};
    for (i = 0; i < len(accumulator); ++i) {
        color *= accumulator[i];
    }
}

void
getCameraRay(export Ray ray;
             const vector throughPos;
             const vector pos;
             const vector u;
             const vector v;
             const float aperture)
{
    vector2 randomPos;
    vector origin;

    randomPos = sample_circle_uniform(set(nrandom(), nrandom()));
    randomPos *= aperture * 0.5;
    origin = pos + u * randomPos.x + v * randomPos.y;
    ray = Ray(origin, normalize(throughPos - origin));
}

cvex
main(export vector Cd = {0.0, 0.0, 0.0};
     const vector P = {0.0, 0.0, 0.0};
     const vector cameraPos = {0.0, 0.0, 0.0};
     const vector cameraU = {1.0, 0.0, 0.0};
     const vector cameraV = {0.0, 1.0, 0.0};
     const float cameraAperture = 1.0)
{
    Ray ray;

    Cd = {0.0, 0.0, 0.0};
    getCameraRay(ray, P, cameraPos, cameraU, cameraV, cameraAperture);
    getColor(Cd, ray);
}
