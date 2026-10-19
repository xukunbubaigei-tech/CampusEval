"""Independent symbolic/numeric checks for specified first-batch MIT answers.

These checks do not certify every sentence or every proof in the dataset.
"""
import json
import math
import runpy
from pathlib import Path
import sympy as s

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'datasets/MIT'
RID=runpy.run_path(str(ROOT/'scripts/construction/mit/build_mit_dataset.py'))['rid']
records={r['id']:r for r in map(json.loads,(DATA/'questions.jsonl').read_text(encoding='utf-8').splitlines())}
checks=[]


def check(key,number,description,condition,answer_fragment=None):
    record=records[RID(key,number)]
    passed=bool(condition) and (answer_fragment is None or answer_fragment in record['answer']['final_answer'])
    checks.append({'id':record['id'],'check':description,'passed':passed})
    if not passed:raise AssertionError(checks[-1])


x,y,z,t,a,beta,r,theta=s.symbols('x y z t a beta r theta', real=True)
check('single',1,'product rule and seventh derivative',s.simplify(s.diff(x**3*s.exp(x),x)-s.exp(x)*(3*x**2+x**3))==0 and s.diff(s.sin(2*x),x,7)==-128*s.cos(2*x),'128')
check('single',2,'tangent slope and point',s.diff(3*x*x-5*x+2,x).subs(x,2)==7 and 7*2-10==4,'7x-10')
check('single',3,'derivative and arctangent limit',s.diff(x/(x+1),x).simplify()==1/(x+1)**2 and s.limit((s.atan(x)-s.pi/3)/(x-s.sqrt(3)),x,s.sqrt(3))==s.Rational(1,4),'1/4')
f=x/(1+x*x)
check('single',4,'graph derivatives and extrema',s.simplify(s.diff(f,x)-(1-x*x)/(1+x*x)**2)==0 and s.simplify(s.diff(f,x,2)-2*x*(x*x-3)/(1+x*x)**3)==0 and f.subs(x,1)==s.Rational(1,2),'(1,1/2)')
check('single',5,'poster minimum',s.diff(82+8*x+200/x,x).subs(x,5)==0 and s.diff(82+8*x+200/x,x,2).subs(x,5)>0,'18')
check('single',7,'Riemann sum integral and FTC',s.integrate(s.sqrt(1+x),(x,0,2))==2*s.sqrt(3)-s.Rational(2,3),'2/3')
check('single',8,'two definite integrals',s.integrate(s.tan(x)*s.sec(x)**2,(x,0,s.pi/4))==s.Rational(1,2) and s.integrate(x*s.log(x),(x,1,2))==2*s.log(2)-s.Rational(3,4),'3/4')
anti=s.Rational(9,2)*s.asin(x/3)-x*s.sqrt(9-x*x)/2
check('single',9,'differentiate antiderivative',s.simplify(s.diff(anti,x)-x*x/s.sqrt(9-x*x))==0,'arcsin')
check('single',10,'cored sphere shell integral, scaled radius a=1',s.integrate(4*s.pi*x*s.sqrt(1-x*x),(x,s.Rational(1,2),1))==s.sqrt(3)*s.pi/2,'a^3/2')
check('single',11,'two-trapezoid arithmetic',abs((2.7+2*6.7+29.7)-45.8)<1e-12,'45.8')
check('single',12,'decay initial mass and half-life',100*2**(-1600/1600)==50,'1600')
check('single',13,'parametric speed',s.trigsimp(s.cos(s.pi*t*t/2)**2+s.sin(s.pi*t*t/2)**2)==1,'t_0')
check('single',14,'Taylor approximation and bounds',s.Rational(1,2)-s.Rational(1,2)**2/2==s.Rational(3,8) and 0<float(s.log(s.Rational(3,2))-s.Rational(3,8))<s.Rational(1,24),'1/24')
check('single',15,'derivative differences for strict inequalities',s.simplify(s.diff(s.atan(x)-x/(1+x*x),x)-2*x*x/(1+x*x)**2)==0 and s.simplify(s.diff(x-s.atan(x),x)-x*x/(1+x*x))==0,'true')
check('multi',1,'plane contains line and point; normalized dot product',s.expand(3*(1+2*t)+2*(2-3*t))==7 and 3*1+2*2==7 and s.Matrix([2,1,1]).dot(s.Matrix([-1,2,-3]))==-3,'-3/')
A=s.Matrix([[1,0,3],[-2,1,-1],[-1,1,a]])
check('multi',3,'determinant, nullspace, inverse row',A.subs(a,2).det()==0 and A.subs(a,2)*s.Matrix([-3,-5,1])==s.zeros(3,1) and list(A.subs(a,1).inv()[1,:])==[-3,-4,5],'p=-4')
v=s.Matrix([s.cos(s.exp(t)),s.sin(s.exp(t)),s.exp(t)]).diff(t)
check('multi',4,'unit tangent and speed',s.trigsimp(v.dot(v)-2*s.exp(2*t))==0,'-e^t')
F=z*s.sqrt(x*x+y)+2*y/z
check('multi',5,'gradient and directional derivative',s.Matrix([s.diff(F,k) for k in (x,y,z)]).subs({x:1,y:3,z:2})==s.Matrix([1,s.Rational(3,2),s.Rational(1,2)]) and s.Matrix([-2,2,-1]).dot(s.Matrix([1,s.Rational(3,2),s.Rational(1,2)]))/3==s.Rational(1,6),'0.6')
f=x+4*y+2/(x*y);point={x:2,y:s.Rational(1,2)}
check('multi',6,'stationarity and positive Hessian determinant',s.diff(f,x).subs(point)==0 and s.diff(f,y).subs(point)==0 and s.hessian(f,(x,y)).subs(point).det()==12,'minimum')
check('multi',8,'chain-rule dot product and nonconservative field',s.Matrix([1,2,-2]).dot(s.Matrix([1,-1,-s.sqrt(2)]))==2*s.sqrt(2)-1 and s.diff(-y,y)!=s.diff(x,x),'2\\sqrt2-1')
check('multi',9,'reversed region area',s.integrate(2*s.sqrt(2*x)-x*x,(x,0,2))==s.integrate(s.sqrt(y)-y*y/8,(y,0,4)),'y^2/8')
u,v=s.symbols('u v',positive=True)
inverse=s.Matrix([u**s.Rational(1,3)*v**s.Rational(-1,3),u**s.Rational(1,3)*v**s.Rational(2,3)])
check('multi',10,'change-of-variable Jacobian',s.simplify(inverse.jacobian([u,v]).det()-s.Rational(1,3)*u**s.Rational(-1,3)*v**s.Rational(-2,3))==0,'u^{-1/3}')
check('multi',11,'divergence flux over triangle',s.integrate(s.integrate(1,(y,0,1-x)),(x,0,1))==s.Rational(1,2),'1/2')
check('multi',12,'cone mass and spherical cone angle',s.integrate(s.integrate(s.integrate(z*r,(z,2*r,2)),(r,0,1)),(theta,0,2*s.pi))==s.pi,'M=\\pi')
potential=x*y-y*z+x*y*y*z
check('multi',13,'potential gradient and endpoint values',s.Matrix([s.diff(potential,k) for k in (x,y,z)])==s.Matrix([y+y*y*z,x-z+2*x*y*z,-y+x*y*y]) and potential.subs({x:1,y:-1,z:2})-potential.subs({x:2,y:2,z:1})==-7,'-7')
check('multi',14,'cylinder flux',s.integrate(s.integrate(4*s.cos(theta)**2,(z,0,4)),(theta,0,s.pi/2))==4*s.pi,'4\\pi')
check('multi',15,'Stokes polar integral',s.integrate(s.integrate(4*(r*r-2)*r,(r,0,2)),(theta,0,s.pi/2))==0,'0')
R=s.Matrix([[1,-2,-5],[0,0,0],[0,0,0]]);E=s.Matrix([[1,0,0],[-3,1,0],[-5,0,1]])
check('quiz1',1,'reconstruct A and b',E.inv()*R==s.Matrix([[1,-2,-5],[3,-6,-15],[5,-10,-25]]) and E.inv()*s.Matrix([4,0,0])==s.Matrix([4,12,20]),'20')
A=s.Matrix([[0,1,2,2],[0,3,8,7],[0,0,4,2]])
check('quiz1',2,'rref and special solutions',A.rref()[0]==s.Matrix([[0,1,0,1],[0,0,1,s.Rational(1,2)],[0,0,0,0]]) and A*s.Matrix([0,-1,s.Rational(-1,2),1])==s.zeros(3,1),'1/2')
check('quiz1',4,'column-space witness',s.Matrix([[2,1],[6,5],[2,4]])*s.Matrix([3,2])==s.Matrix([8,28,14]),'(3,2)')
a=s.Matrix([2,1,3]);P=a*a.T/14
check('quiz2',1,'projection idempotence, kernel basis, trace',P*P==P and P*s.Matrix([3,0,-2])==s.zeros(3,1) and P*s.Matrix([-1,2,0])==s.zeros(3,1) and s.trace(P)==1,'3z=0')
A=s.Matrix([[1,1],[1,1]])
check('quiz2',2,'dependent-columns counterexample has one projection and nonunique coefficients',A*s.Matrix([1,0])==A*s.Matrix([0,1]) and A.det()==0,'remains unique')
check('quiz2',3,'determinants, inverse entry, orthogonal eigenvectors',all((s.eye(n)-s.ones(n)).det()==1-n for n in range(2,8)) and (s.eye(4)-s.ones(4)).inv()[0,0]==s.Rational(2,3) and s.Matrix([1,-1,0]).dot(s.Matrix([1,1,-2]))==0,'2/3')
u=s.Matrix([s.Rational(3,5),s.Rational(4,5)]);H=s.eye(2)-2*u*u.T
check('quiz3',1,'reflection identities on a nontrivial unit vector',H*H==s.eye(2) and H*u==-u and s.trace(H)==0,'n-2')
A=s.Matrix([[2,1],[1,2]]);B=A.row_join(A).col_join(A.row_join(A))
check('quiz3',2,'positive-definite inverse and semidefinite block example',set(A.inv().eigenvals())=={s.Rational(1,3),s.Integer(1)} and B.det()==0 and all(l>=0 for l in B.eigenvals()),'singular')
A=s.Matrix([[0,-1],[4,0]]);U=s.Matrix([[0,-1],[1,0]])
solution=s.Matrix([2*s.cos(2*t),4*s.sin(2*t)])
check('quiz3',3,'eigenvalues, ODE and SVD reconstruction',A.charpoly().as_expr()==s.Symbol('lambda')**2+4 and solution.diff(t)==A*solution and U*s.diag(4,1)==A,'4\\sin2t')
check('stats1',2,'password adjacency counting',s.Rational(9,s.binomial(10,2))==s.Rational(1,5),'1/5')
check('stats1',3,'joint probabilities and conditional probability',4*(s.Rational(5,32)+s.Rational(1,16))+2*s.Rational(1,16)==1 and s.Rational(5,32)/s.Rational(7,32)==s.Rational(5,7),'5/7')
check('stats1',4,'Bayes positive predictive probability',s.Rational(7,10)*s.Rational(2,100)/(s.Rational(7,10)*s.Rational(2,100)+s.Rational(1,10)*s.Rational(98,100))==s.Rational(1,8),'0.125')
joint=s.Rational(5,4)-x*y;mx=s.integrate(joint,(y,0,1));mean=s.integrate(x*mx,(x,0,1));var=s.integrate(x*x*mx,(x,0,1))-mean**2;cov=s.integrate(s.integrate(x*y*joint,(x,0,1)),(y,0,1))-mean**2
check('stats1',5,'density normalization, mean, variance, covariance and correlation',s.integrate(mx,(x,0,1))==1 and mean==s.Rational(11,24) and var==s.Rational(47,576) and cov==s.Rational(-5,576) and cov/var==s.Rational(-5,47),'-5/47')
check('stats1',6,'CLT total variance and normal tail',20*5*10**4==1000**2 and abs(.5*math.erfc(.5/math.sqrt(2))-.3085)<.0001,'0.3085')
check('stats2','I_2','type-II error from power',s.Rational(1)-s.Rational(95,100)==s.Rational(5,100),'0.05')
beta_kernel=x**2*(1-x)**3*s.binomial(10,4)*x**4*(1-x)**6
normalizer=s.integrate(beta_kernel,(x,0,1))
beta_example=s.simplify(beta_kernel/normalizer-x**6*(1-x)**9/s.beta(7,10).expand(func=True))
gamma_kernel=beta*s.exp(-3*beta)*beta*s.exp(-2*beta)
gamma_example=s.integrate(gamma_kernel,(beta,0,s.oo))
check('stats2','I_5','normalized beta-binomial and gamma-exponential posterior examples',beta_example==0 and gamma_example==s.Rational(2,125),'both')
check('stats2','II_1','gamma MLE score root and concavity',s.diff(15*s.log(beta)-12*beta,beta).subs(beta,s.Rational(5,4))==0 and s.diff(15*s.log(beta)-12*beta,beta,2).subs(beta,s.Rational(5,4))<0,'5/4')
check('stats2','II_2','posterior normalization',s.integrate(56*x**6*(1-x),(x,0,1))==1,'56')
check('stats2','II_3','posterior odds likelihood ratio',s.Rational(1,100)*10==s.Rational(1,10),'1/10')
check('stats2','II_4','standard normal tail and rejection',abs(.5*math.erfc(2/math.sqrt(2))-.0228)<.0001 and .0228<.1,'Reject')
check('stats2','II_5','chi-square statistic and df=1 tail',25/10+25/10+25/40+25/40==6.25 and .01<math.erfc(math.sqrt(6.25/2))<.025,'6.25')
report={'passed':all(c['passed'] for c in checks),'check_count':len(checks),
        'records_with_computational_checks':len({c['id'] for c in checks}),
        'scope':'Only the listed symbolic/numeric checks; numerical matrix examples are not universal proofs. Conceptual answers and full source fidelity require review.',
        'checks':checks}
(DATA/'mathematical_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False))
