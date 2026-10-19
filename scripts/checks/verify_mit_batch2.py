"""Independent calculations for the listed second-batch MIT numerical results.

Finite examples check identities but do not replace proofs or visual review.
"""
import itertools
import json
import math
from pathlib import Path
import mpmath as mp
import sympy as s

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'datasets/MIT'
rows={r['id']:r for r in map(json.loads,(OUT/'questions.jsonl').read_text(encoding='utf-8').splitlines())}
checks=[]
PREFIX={'p':'mit_1805_s2022_practice1_all','st':'mit_1805_s2022_practice2a',
        'm':'mit_1802sc_f2010_practicefinal','l':'mit_1806_s2010_final','f':'mit_1805_s2022_final'}


def check(group,n,label,condition,fragment=None):
    ident=f'{PREFIX[group]}_{n:02d}' if isinstance(n,int) else f'{PREFIX[group]}_{n}'
    answer=rows[ident]['answer']['final_answer']
    ok=bool(condition) and (fragment is None or fragment in answer)
    checks.append({'id':ident,'check':label,'passed':ok})
    if not ok:raise AssertionError(checks[-1])


R=s.Rational
x,y,z,a,b,p,lam,t=s.symbols('x y z a b p lam t',real=True)
pos=s.symbols('q',positive=True)
Phi=lambda q:.5*mp.erfc(-q/mp.sqrt(2))
Ttail=lambda q,df:mp.betainc(df/2,.5,0,df/(df+q*q),regularized=True)/2
ChiTail=lambda q,df:mp.gammainc(df/2,q/2,mp.inf)/mp.gamma(df/2)
vals=range(-2,3);probs=[R(k,15) for k in range(1,6)]
mean=sum(v*w for v,w in zip(vals,probs));variance=sum((v-mean)**2*w for v,w in zip(vals,probs))
check('p',26,'discrete mean and variance from probability table',mean==R(2,3) and variance==R(14,9),'14/9')
mom=lambda k:s.integrate(2*x*x**k,(x,0,1))
check('p',27,'continuous second and fourth moments',mom(2)-mom(1)**2==R(1,18) and mom(4)-mom(2)**2==R(1,12),'1/12')
check('p',28,'push-forward pmf and variance',R(1,8)+R(5,8)==R(3,4) and R(3,4)-R(1,2)**2==R(1,2),'1/2')
check('p',30,'Bernoulli moments',sum(v*w for v,w in [(0,1-p),(1,p)])==p and s.expand(p-p**2-p*(1-p))==0,'p(1-p)')
check('p',31,'indicator expectations without independence',100*R(1,100)==1,'1')
check('p',32,'geometric normalization and growing wager expectation partial sums',sum(R(1,2)**(k+1) for k in range(50))==1-R(1,2)**50 and sum(2**k*R(1,2)**(k+1) for k in range(50))==25,'infty')
check('p',33,'independent blocks versus scaling variance',9*100*R(1,6)*R(5,6)==125 and 144*25*R(1,6)*R(5,6)==500,'500')
check('p',34,'even-support binomial push-forward, n=7',sum(s.binomial(7,k)*R(1,2)**7 for k in range(8))==1,'y/2')
check('p',35,'affine uniform density and cdf boundaries',s.integrate(R(1,2),(y,5,7))==1 and ((y-5)/2).subs(y,7)==1,'1/2')
check('p',36,'square of an exponential: differentiate cdf',s.simplify(s.diff(1-s.exp(-pos*s.sqrt(x)),x)-pos*s.exp(-pos*s.sqrt(x))/(2*s.sqrt(x)))==0,'2\\sqrt y')
mean=R(1,10)*2+R(6,10)*3
check('p',37,'discrete nonlinear transform moments',mean==2 and R(1,10)*4+R(6,10)*9-mean**2==R(18,10) and R(4,10)*3+R(6,10)*12==R(84,10),'8.4')
check('p',38,'reciprocal exponential cdf derivative',s.simplify(s.diff(s.exp(-2/x),x)-2*s.exp(-2/x)/x**2)==0,'r^{-2}')
check('p',39,'polynomial density normalization and interval probability',s.integrate(x+R(3,2)*x*x,(x,0,1))==1 and s.integrate(x+R(3,2)*x*x,(x,R(1,2),1))==R(13,16),'13/16')
check('p',40,'Bernoulli convolution',R(1,2)*R(2,3)==R(1,3) and R(1,2)*R(1,3)+R(1,2)*R(2,3)==R(1,2),'1/6')
check('p',42,'cdf jumps sum to one',R(1,5)+(R(2,5)-R(1,5))+(1-R(2,5))==1,'3/5')
F=2*x*x-x**4
check('p',45,'cdf difference and derivative',F.subs(x,R(3,4))-F.subs(x,R(1,4))==R(11,16) and s.diff(F,x)==4*x-4*x**3,'11/16')
check('p',46,'exponential memorylessness',s.simplify(s.exp(-15*pos)/s.exp(-10*pos)-s.exp(-5*pos))==0,'e^{-5')
cdf=(1+s.erf(s.log(x)/s.sqrt(2)))/2
check('p',48,'lognormal cdf derivative and median',s.simplify(s.diff(cdf,x)-s.exp(-s.log(x)**2/2)/(x*s.sqrt(2*s.pi)))==0 and cdf.subs(x,1)==R(1,2),'1')
normal=s.exp(-x*x/2)/s.sqrt(2*s.pi)
check('p',49,'Gaussian fourth moment and square-sum normal tail',s.integrate(x**4*normal,(x,-s.oo,s.oo))==3 and abs(1-Phi(1/mp.sqrt(2))-.23975)<.00001,'0.23975')
mu=s.symbols('mu',real=True);sigma=s.symbols('sigma',positive=True)
cdf=(1+s.erf((x-mu)/(sigma*s.sqrt(2))))/2
check('p',50,'normal cdf change of variables',s.simplify(cdf.subs(x,mu+sigma*z)-(1+s.erf(z/s.sqrt(2)))/2)==0,'N(0,1)')
check('p',51,'normal linear combination moments and probability',3*2-2*5+1==-3 and 9*5+4*9==81 and abs(Phi(1)-.8413)<.0001,'81')
mean=s.integrate(x,(x,a,b))/(b-a);ex2=s.integrate(x*x,(x,a,b))/(b-a)
check('p',52,'symbolic uniform moment integrals',s.simplify(mean-(a+b)/2)==0 and s.simplify(ex2-mean**2-(b-a)**2/12)==0,'(b-a)^2/12')
check('p',53,'binomial convolution for n=2,m=3',all(s.simplify(sum(s.binomial(2,j)*s.binomial(3,k-j) for j in range(3))-s.binomial(5,k))==0 for k in range(6)),'n+m')
check('p',54,'exponential median cdf',s.simplify(1-s.exp(-pos*(s.log(2)/pos))-R(1,2))==0,'ln2')
check('p',55,'Pareto tail and quantile',s.integrate(x**-2,(x,5,s.oo))==R(1,5),'5')
joint=R(2,243)*x*x*y*(1+y)
check('p',58,'joint density normalizer and rectangle probability',s.integrate(s.integrate(joint,(x,0,3)),(y,0,3))==1 and s.integrate(s.integrate(joint,(x,1,2)),(y,0,1))==R(35,2187),'35/2187')
r,ss,tt,u,mx,my=s.symbols('r ss tt u mx my')
check('p',59,'centered affine covariance integrand identity',s.expand((r*x+ss-(r*mx+ss))*(tt*y+u-(tt*my+u))-r*tt*(x-mx)*(y-my))==0,'hold')
check('p',60,'covariance product expansion',s.expand((x-mx)*(y-my)-(x*y-mx*y-my*x+mx*my))==0,'E[XY]')
A=s.Matrix([[R(1,6),0,R(1,6)],[0,R(1,4),R(1,12)],[0,R(1,12),R(1,4)]])
check('p',61,'joint table margins',all(sum(A[i,j] for j in range(3))==R(1,3) for i in range(3)) and [sum(A[i,j] for i in range(3)) for j in range(3)]==[R(1,6),R(1,3),R(1,2)],'1/12')
check('p',62,'three joint pmf event sums',sum(R(2*i,80) for i in range(1,5))==R(1,4) and 2*R(5,80)==R(1,8) and sum(R(i+j,80) for i in [1,2] for j in [3,4])==R(1,4),'1/8')

def coin_cov(n,fun1,fun2):
    samples=list(itertools.product([0,1],repeat=n));den=2**n
    a=[fun1(v) for v in samples];b=[fun2(v) for v in samples]
    ea=R(sum(a),den);eb=R(sum(b),den)
    cov=R(sum(i*j for i,j in zip(a,b)),den)-ea*eb
    va=R(sum(i*i for i in a),den)-ea*ea;vb=R(sum(i*i for i in b),den)-eb*eb
    return cov,s.simplify(cov/s.sqrt(va*vb))

check('p',63,'enumerate three-toss shared/disjoint counts',coin_cov(3,lambda v:v[0],lambda v:v[1]+v[2])[0]==0 and coin_cov(3,lambda v:v[0],lambda v:v[0]+v[1])[0]==R(1,4),'1/4')
check('p',64,'dependent but uncorrelated nonlinear transform',sum(i**3 for i in range(-2,3))==0 and R(sum(i*i for i in range(-2,3)),5)==2,'covariance 0')
joint=x+y;ex=s.integrate(s.integrate(x*joint,(x,0,1)),(y,0,1));exy=s.integrate(s.integrate(x*y*joint,(x,0,1)),(y,0,1))
check('p',65,'joint moments and covariance',ex==R(7,12) and exy-ex**2==R(-1,144) and s.integrate(s.integrate((x*x+y*y)*joint,(x,0,1)),(y,0,1))==R(5,6),'-1/144')
check('p',66,'enumerate overlapping pairs',coin_cov(3,lambda v:sum(v[:2]),lambda v:sum(v[1:]))==(R(1,4),R(1,2)),'1/2')
check('p',67,'enumerate overlapping triples',coin_cov(5,lambda v:sum(v[:3]),lambda v:sum(v[2:]))==(R(1,4),R(1,3)),'1/3')
check('p',69,'CLT standardization',R(30-20,1)/R(10,3)==3 and abs(Phi(3)-.99865)<.00001,'0.99865')
# Long-list 71 is excluded as a pure parameter variant of 69.
check('p',72,'continuity correction comparison',abs(Phi((30.5-100/3)/mp.sqrt(200/9))-.27390)<.00001 and abs(Phi(-1/mp.sqrt(2))-.23975)<.00001,'0.27390')
check('p',73,'normal extreme tail as approximation',abs(.5*mp.erfc(10/mp.sqrt(2))/mp.mpf('7.62e-24')-1)<.001,'10^{-24}')
pl=sum(math.comb(45,k) for k in range(28,46))/2**45;ps=sum(math.comb(15,k) for k in range(10,16))/2**15
check('p',74,'binomial hospital daily tails and annual moments',ps>pl and .067<pl<.069 and .150<ps<.152 and 24<365*pl<26 and 54<365*ps<56,'s=0')

check('st',1,'normal table probabilities and critical cdf values',abs(Phi(1.625)-.9479)<.0001 and abs(Phi(1.64485)-.95)<.00001 and abs(Phi(.67449)-.75)<.00001,'1.28155')
check('st',2,'Student t tail approximations',.1<Ttail(1.6,3)<.11 and abs((1-2*Ttail(1.68,49))-.9)<.002 and abs((1-2*Ttail(1.6,49))-.88)<.005,'1.86')
check('st',3,'chi-square tails and critical boundaries',abs(ChiTail(1.6,3)-.6594)<.0001 and abs(ChiTail(20,16)-.2202)<.0001 and abs(ChiTail(15.51,8)-.05)<.001,'0.2202')
check('st',4,'sample variance and median',sum((i-4)**2 for i in [5,1,3,3,8])/4==7 and sorted([5,1,3,3,8])[2]==3,'sqrt7')
ll=62*s.log(x)+38*s.log(1-x)
check('st',5,'binomial likelihood score',s.diff(ll,x).subs(x,R(62,100))==0 and s.diff(ll,x,2).subs(x,R(62,100))<0,'0.62')
check('st',6,'discrete uniform likelihood monotonicity',all(R(1,N)**5>R(1,N+1)**5 for N in range(7,15)),'max')
check('st',7,'exponential likelihood score and concavity',s.diff(5*s.log(x)-12*x,x).subs(x,R(5,12))==0 and s.diff(5*s.log(x)-12*x,x,2).subs(x,R(5,12))<0,'sum')
ll=8*s.log(x-1)-13*s.log(x)
check('st',8,'geometric likelihood score at sample mean',s.diff(ll,x).subs(x,R(13,5))==0 and s.diff(ll,x,2).subs(x,R(13,5))<0,'bar x')
check('st',9,'without-replacement likelihood monotonicity',all(s.binomial(N,3)<s.binomial(N+1,3) for N in range(7,15)),'7')
check('st',10,'twin posterior probability and odds',R(1,4)/(R(1,4)+R(3,4)/2)==R(2,5) and R(1,3)*2==R(2,3),'2/3')
weights=[R(2,36),R(10,64),R(2,144),R(1,400)];total=sum(weights);post=[w/total for w in weights]
check('st',11,'dice posterior and predictive mixtures',abs(float(post[1])-.68472)<.00001 and abs(float(sum(w/n for w,n in zip(post,[6,8,12,20])))-.13179)<.00001 and abs(float(post[-1]/20)-.0005478)<.0000001,'0.13179')
check('st',12,'HHHT posterior odds and prediction',R(1,2)**4/(R(3,4)**3/4)==R(16,27) and R(16,43)/2+R(27,43)*R(3,4)==R(113,172),'113/172')
kernel=R(math.factorial(13),math.factorial(7)*math.factorial(5))*x**7*(1-x)**5
check('st',13,'beta posterior normalization, MAP and interval endpoints',s.integrate(kernel,(x,0,1))==1 and s.diff(s.log(x**7*(1-x)**5),x).subs(x,R(7,12))==0 and abs(mp.betainc(8,6,0,.48330,regularized=True)-.25)<.00002 and abs(mp.betainc(8,6,0,.77604,regularized=True)-.95)<.00002,'Beta}(8,6)')
check('st',14,'two sequential posterior normalizations',s.integrate(3*(1-x)**2,(x,0,1))==1 and s.integrate(4*(1-x)**3,(x,0,1))==1,'4(1-')
check('st',15,'binomial evidence and normalized beta posterior',s.integrate(s.binomial(20,16)*x**16*(1-x)**4,(x,0,1))==R(1,21),'17,5')
check('st',16,'normal posterior precision and minimum sample count',R(9+10000*10,10001)==R(100009,10001) and R(1,1+10000*99)>R(1,10**6) and R(1,1+10000*100)<R(1,10**6),'100')
check('st',17,'z statistic and two-sided probability',abs(2*(1-Phi(1.575))-.1152)<.0001,'1.575')
check('st',18,'Student t p-value correction',abs(2*Ttail(2.625,48)-.0116)<.00002 and .01<2*Ttail(2.625,48)<.05,'0.0116')

check('m',1,'three-point plane cross product',s.Matrix([0,1,1]).cross(s.Matrix([-3,1,3]))==s.Matrix([2,-3,3]) and 2-3-3==-4,'-4')
A=s.Matrix([[1,0,a],[2,a,1],[1,-1,2]])
check('m',2,'singularity parameters and inverse marked entry',A.det()==1-a*a and A.subs(a,2).inv()[2,1]==R(-1,3),'-1/3')
v=s.Matrix([-3*s.sin(t),5*s.cos(t),-4*s.sin(t)])
check('m',4,'constant speed and plane crossings',s.trigsimp(v.dot(v))==25 and s.cos(s.pi/2)==0,'5')
F=x*x*y-x*y**3;grad=s.Matrix([s.diff(F,q) for q in [x,y]]).subs({x:2,y:1})
check('m',5,'gradient and normalized directional derivative',grad.dot(s.Matrix([R(3,5),R(4,5)]))==R(1,5),'0.002')
check('m',6,'corrected surface gradient and tangent plane',s.Matrix([s.diff(x*x+2*y*y+2*z*z,q) for q in [x,y,z]]).subs({x:1,y:1,z:1})==s.Matrix([2,4,4]),'2/3')
check('m',7,'nearest plane point is parallel to normal',s.Matrix([2,1,-1]).dot(s.Matrix([2,1,-1]))==6,'(2,1,-1)')
check('m',8,'implicit derivative and constrained chain rule',-R(2,-1)==2 and 1+2*2==5,'5')
check('m',9,'reversed integral evaluation',s.integrate(y*s.exp(-y*y)/2,(y,0,9))==(1-s.exp(-81))/4,'e^{-81}')
check('m',11,'linear-field divergence condition',s.diff(a*x,x)+s.diff(b*y,y)==a+b,'a+b=1')
phi,rho=s.symbols('phi rho',real=True)
check('m',12,'gravitational force component integral',s.integrate(rho,(rho,0,1))*s.integrate(s.cos(phi)**2*s.sin(phi),(phi,0,s.pi/2))*2*s.pi==s.pi/3,'pi G/3')
check('m',13,'parametric line integral',s.integrate(2*t-28*t,(t,0,1))==-13,'-13')
potential=x*y*y+y*y*z+z**3/3
check('m',14,'potential gradient',(s.Matrix([s.diff(potential,q) for q in [x,y,z]])-s.Matrix([y*y,2*y*(x+z),y*y+z*z])).applyfunc(s.simplify)==s.zeros(3,1),'a=b=1')
check('m','15_16','direct flux equals divergence flux',s.integrate((x*x+1)*x,(x,0,1))*2*s.pi==3*s.pi/2,'3\\pi/2')
check('m',18,'Gaussian quadrant polar integral',s.integrate(s.exp(-x*x)*x,(x,0,s.oo))*s.pi/2==s.pi/4,'sqrt\\pi/2')
A=s.Matrix([[1,1],[1,2],[1,4]])
check('l',2,'least-squares fit and zero-projection data',A.T*A*s.Matrix([8,-2])==A.T*s.Matrix([6,4,0]) and A.T*s.Matrix([2,-3,1])==s.zeros(2,1),'C=8,D=-2')
V=s.Matrix([[1,2],[0,1]]);B=s.Matrix([[2,1],[3,4]])
check('l',3,'matrix recovery and inverse multiplication',B*V.inv()*V==B and (B*V.inv()).inv()==V*B.inv(),'BV^{-1}')
M=s.Matrix([[3,-4],[2,-3]]);sol=s.exp(t)*s.Matrix([2,1])-s.exp(-t)*s.Matrix([1,1]);A=s.Matrix([[R(4,5),R(1,10)],[R(1,5),R(9,10)]])
check('l',4,'ODE corrected sign and stationary distribution',sol.subs(t,0)==s.Matrix([1,0]) and sol.diff(t)==M*sol and A*s.Matrix([R(1,3),R(2,3)])==s.Matrix([R(1,3),R(2,3)]),'-e^{-t}')
A=s.Matrix([[0,0,1],[1,0,0],[0,1,0]]);normal=s.Matrix([1,2,1]);P=s.eye(3)-normal*normal.T/6
check('l',5,'cyclic rotation and projection eigenpairs',A**3==s.eye(3) and P*normal==s.zeros(3,1) and P*s.Matrix([-2,1,0])==s.Matrix([-2,1,0]) and P*s.Matrix([1,-1,1])==s.Matrix([1,-1,1]),'eigenvalue 1')
A=s.Matrix([[1,2],[2,4],[3,6]]);Q=s.Matrix.hstack(s.Matrix([1,2,3])/s.sqrt(14),s.Matrix([-2,1,0])/s.sqrt(5),s.Matrix([3,6,-5])/s.sqrt(70))
check('l',6,'orthonormal eigenbasis and Gram-Schmidt dependence',Q.T*Q==s.eye(3) and Q.T*(A*A.T)*Q==s.diag(70,0,0) and A.rank()==1,'70')
C=s.Matrix([[x,1,1,1],[1,1,1,1],[1,1,1,0],[1,1,0,0]])
check('l',7,'symbolic determinant and cofactor',C.det()==1-x and C.cofactor(0,0)==-1,'1-x')
S=s.Matrix([[1,2,0],[0,1,1],[0,0,1]]);D=s.diag(2,3,4)
check('l',8,'conjugated diagonal basis example',S.inv()*(S*D*S.inv())*S==D,'SE_{11}')
check('f',1,'binomial no-six, one-six and mean',sum(s.binomial(8,k)*R(1,6)**k*R(5,6)**(8-k) for k in range(9))==1 and 8*R(1,6)==R(4,3),'4/3')
f=R(3,7)*x*x
check('f',2,'polynomial density mean and cdf',s.integrate(f,(x,1,2))==1 and s.integrate(f,(x,1,R(3,2)))==R(19,56) and s.integrate(x*f,(x,1,2))==R(45,28),'45/28')
check('f',3,'sum variance, correlation and standardization',36+49==85 and 36+49+42==127 and R(21,6*7)==R(1,2),'127')
check('f',5,'Pareto MLE score and boundary',s.diff(5*s.log(x)-(x+1)*12,x).subs(x,R(5,12))==0,'sum')
check('f',6,'diagnostic odds update',R(1,99)*25==R(25,99),'25/99')
check('f',7,'Bayes filter update and predictive color probability',sum(R(a,20)*R(b,10) for a,b in zip([3,7,7,3],[3,3,7,7]))==R(1,2),'7/20')
stat=sum(R((o-e)**2,e) for o,e in zip([180,190,185,160,165,120],[200,200,200,150,150,100]))
check('f',8,'chi-square fit statistic and tail',stat==R(235,24) and abs(ChiTail(float(stat),5)-.0814)<.0001,'235/24')
check('f',9,'pooled variance, standard error and t tail',(10*64+10*36)/20==50 and abs(2*Ttail(mp.sqrt(11)/2,20)-.1129)<.0001,'1.6583')
check('f',10,'polling margin conventions',math.ceil((1.96/(2*.05))**2)==385 and (1/.05)**2==400,'385')
check('f',11,'power from alternative distribution',abs((1-(Phi(-2.04)-Phi(-5.96)))-.9793)<.0001,'0.9793')
check('f',12,'absolute-value regression least-squares coefficient',R(2*1+4*R(3,2)+2*R(1,2),2**2+4**2+2**2)==R(3,8),'3/8')
nums=[float(v) for v in __import__('re').findall(r'\b\d+\.\d{3}\b',rows[PREFIX['f']+'_13']['question']['text'])]
check('f',13,'bootstrap nearest-rank interval from all 100 supplied values',len(nums)==100 and nums[24]==6.740 and nums[74]==7.224,'6.740')
report={'passed':all(c['passed'] for c in checks),'check_count':len(checks),
  'records_with_checks':len({c['id'] for c in checks}),'checks':checks,
  'scope':'Listed symbolic/numeric checks only. Finite matrix/binomial examples do not prove universal assertions. Source figures and conceptual questions require visual/manual review.'}
(OUT/'batch2_mathematical_checks.json').write_bytes((json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False))
