"""Independent symbolic/numeric checks for the explicitly corrected formulas.

These checks cover the listed claims, not every mathematical statement in the
805-record OCR import. The distinction is preserved in the report.
"""
import json
from pathlib import Path
import sympy as s
import mpmath as mp

checks = []


def equal(name, lhs, rhs):
    print("Checking " + name, flush=True)
    residual = s.simplify(lhs-rhs)
    assert residual == 0, (name, residual)
    checks.append(name)


def main():
    x, y, z = s.symbols("x y z", real=True)
    a = s.symbols("a", positive=True)
    c1, c2, c3 = s.symbols("C1 C2 C3")
    n1, n2 = s.Matrix([0,1,1]), s.Matrix([1,2,1])
    normal = s.Matrix([1,-1,1])
    equal("1987平面法向量与两直线方向正交1", normal.dot(n1), 0)
    equal("1987平面法向量与两直线方向正交2", normal.dot(n2), 0)
    f = c1+s.exp(-3*x)*(c2*s.cos(a*x)+c3*s.sin(a*x))+x/(9+a*a)
    equal("1987三阶ODE通解代回", s.diff(f,x,3)+6*s.diff(f,x,2)+(9+a*a)*s.diff(f,x), 1)
    g = -s.log(1-x/2)/x
    equal("1987级数在0的连续值", s.limit(g,x,0), s.Rational(1,2))
    for n in range(1,7):
        equal(f"1987和函数Taylor系数{n}", s.expand(s.series(g,x,0,7).removeO()).coeff(x,n-1), 1/(s.Integer(n)*2**n))
    f = (1-2*x)*s.exp(x)
    equal("1988二阶ODE代回", s.diff(f,x,2)-3*s.diff(f,x)+2*f, 2*s.exp(x))
    equal("1988二阶ODE初值", f.subs(x,0), 1)
    equal("1988二阶ODE初始斜率", s.diff(f,x).subs(x,0), -1)
    t = s.symbols("t", real=True)
    equal("1997矩阵行列式", s.Matrix([[1,2,-2],[4,t,3],[3,-1,1]]).det(), 7*(t+3))
    r = s.symbols("r", nonnegative=True)
    equal("1997三重积分", 2*s.pi*s.integrate(s.integrate(r**3,(r,0,s.sqrt(2*z))),(z,0,8)), 1024*s.pi/3)
    field = s.Matrix([z-y,x-z,x-y])
    curl = s.Matrix([s.diff(field[2],y)-s.diff(field[1],z),s.diff(field[0],z)-s.diff(field[2],x),s.diff(field[1],x)-s.diff(field[0],y)])
    assert curl == s.Matrix([0,0,2])
    checks.append("1997曲线积分旋度与方向")
    v1, v2 = s.Matrix([1,1,2,3])/s.sqrt(15),s.Matrix([-2,1,5,-3])/s.sqrt(39)
    equal("1997正交基第一列范数",v1.dot(v1),1)
    equal("1997正交基第二列范数",v2.dot(v2),1)
    equal("1997正交基内积",v1.dot(v2),0)
    A=s.Matrix([[2,-1,2],[5,-3,3],[-1,0,-2]])
    l=s.symbols("l")
    equal("1997特征多项式",(l*s.eye(3)-A).det(),(l+1)**3)
    assert (A+s.eye(3)).rank()==2
    checks.append("1997特征空间维数")
    U=s.Matrix([[l,1,1],[1,l,1],[1,1,l]])
    V=s.Matrix([[l,1,1],[1,l,l],[1,1,l*l]])
    equal("2022向量组一行列式",U.det(),(l-1)**2*(l+2))
    equal("2022向量组二行列式",V.det(),(l-1)**2*(l+1)**2)
    for value in [-2,-1,1]:
        assert (U.subs(l,value).rank()==V.subs(l,value).rank()) == (value==1)
    checks.append("2022向量组奇异参数秩")
    primitive=2*s.sqrt(x)*s.log(x)-4*s.sqrt(x)
    equal("2022定积分原函数",s.diff(primitive,x),s.log(x)/s.sqrt(x))
    equal("2022定积分端点",primitive.subs(x,s.exp(2))-primitive.subs(x,1),4)
    f=2*x+s.exp(1-s.sqrt(x))
    equal("2022一阶ODE代回",s.diff(f,x)+f/(2*s.sqrt(x)),2+s.sqrt(x))
    equal("2022一阶ODE初值",f.subs(x,1),3)
    equal("2022渐近线",s.limit(f-2*x,x,s.oo),0)
    theta=s.symbols("theta", real=True)
    equal("2022二重积分圆盘部分",2*s.integrate(1-s.sin(2*theta),(theta,0,s.pi/2)),s.pi-2)
    equal("2022二重积分三角形部分",s.integrate(2,(theta,s.pi/2,s.pi)),s.pi)
    field=s.Matrix([y*z*z-s.cos(z),2*x*y*y,2*x*y*z+x*s.sin(z)])
    curl=s.Matrix([s.diff(field[2],y)-s.diff(field[1],z),s.diff(field[0],z)-s.diff(field[2],x),s.diff(field[1],x)-s.diff(field[0],y)])
    assert curl==s.Matrix([2*x*z,0,2*y*y-z*z])
    equal("2022Stokes积分",s.integrate(s.integrate((3*r*r-1)*r,(r,0,1)),(theta,0,s.pi/2)),s.pi/8)
    v=s.Matrix([1,2,3]); A=v*v.T
    Q=s.Matrix.hstack(v/s.sqrt(14),s.Matrix([2,-1,0])/s.sqrt(5),s.Matrix([3,6,-5])/s.sqrt(70))
    assert s.simplify(Q.T*Q)==s.eye(3)
    assert s.simplify(Q.T*A*Q)==s.diag(14,0,0)
    checks.extend(["2022正交矩阵Q核验","2022二次型标准形核验"])
    mp.mp.dps=30
    values=[mp.quad(lambda u:u/(2*(1+mp.cos(u))),[0,1]),mp.quad(lambda u:mp.log(1+u)/(1+mp.cos(u)),[0,1]),mp.quad(lambda u:2*u/(1+mp.sin(u)),[0,1])]
    assert values[0]<values[1]<values[2]
    checks.append("2022积分大小关系数值交叉核验")
    path=Path(__file__).resolve().parents[2]/"datasets/kaoyan/correction_verification.json"
    path.write_text(json.dumps({"passed":True,"checks_count":len(checks),"checks":checks,
                    "numeric_integrals_2022_q4":[str(v) for v in values],
                    "scope":"仅核验所列校正公式，不等于全部805题完成独立数学审校"},ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Passed {len(checks)} correction checks")


if __name__=="__main__":
    main()
