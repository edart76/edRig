
// functions to align geometry and components

function vector bboxalign(vector alignDir; float padding;
    vector alignMin; vector alignMax;
    vector refMin; vector refMax)
    {
    // align two bounding boxes
    alignDirection.x = int(alignDirection.x);
    alignDirection.y = int(alignDirection.y);
    alignDirection.z = int(alignDirection.z);

    // length of padding
    vector padVec = -alignDirection * padding;

    // check sign of direction
    float dirSign = sign( sum(alignDirection) );
    if (dirSign < 0){
        bMin = bMax;
        refMax = refMin;
        }

    // align
    vector t = -dirSign * (bMin * alignDirection +
        refMax * -alignDirection + padVec);
    return t;
}
