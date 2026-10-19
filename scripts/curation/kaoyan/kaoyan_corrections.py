"""Explicitly disclosed, user-authorized corrections to local source material.

These are editorial mathematical corrections, never official answer claims.
An empty solution remains empty when the annual source supplies no derivation.
"""
CORRECTIONS = {}


def add(y, major, number, final, basis, *, question=None, options=None, solution=None):
    item = {"final_answer": final, "verification_basis": basis,
            "review_status": "corrected_or_manually_rechecked",
            "origin": "本地原页核对及用户授权的数学校正；非官方解答身份声明"}
    if question is not None:
        item["question_text"] = question
    if options is not None:
        item["options"] = [{"label": label, "text": text} for label, text in zip("ABCD", options)]
    if solution is not None:
        item["solution"] = solution
    CORRECTIONS[(y, major, number)] = item


add(1987, 1, 1, r"$x-y+z=0$",
    "两直线方向向量分别为(0,1,1)、(1,2,1)，叉积为(-1,1,-1)；过原点常数项为0。原答案PDF第1页写成x-y+5=0。", solution="")
add(1987, 4, 0, r"$y=C_1+e^{-3x}[C_2\cos(ax)+C_3\sin(ax)]+\frac{x}{9+a^2}$",
    "特征多项式r[r²+6r+9+a²]；直接代回原微分方程验证。原解析的2r²及漏写a均已校正。",
    solution=r"对应齐次方程的特征方程为 $r[(r+3)^2+a^2]=0$，根为 $0,-3\pm ai$。取特解 $y_p=x/(9+a^2)$，代入左端等于1。因此通解为 $y=C_1+e^{-3x}[C_2\cos(ax)+C_3\sin(ax)]+x/(9+a^2)$。")
add(1987, 6, 0, r"收敛域为 $[-2,2)$；$S(x)=-\frac{\ln(1-x/2)}{x}$（$x\ne0$），$S(0)=\frac12$。",
    "合集第3页明确为x^(n-1)，年度解析误作x^(n+1)。使用sum(t^n/n)=-ln(1-t)，另查两端点与x=0。",
    solution=r"令 $t=x/2$。当 $|x|<2$ 且 $x\ne0$ 时，$S(x)=x^{-1}\sum_{n\ge1}(x/2)^n/n=-\ln(1-x/2)/x$。$x=0$ 时仅首项非零，故 $S(0)=1/2$。$x=-2$ 为交错调和型收敛，$x=2$ 为调和型发散，得到收敛域 $[-2,2)$。")
add(1987, 10, 3, r"$E(X)=1$，$D(X)=\frac12$。",
    "配方得exp[-(x-1)²]/sqrt(pi)，与正态密度比较，均值1、方差1/2。原材料此题答案与解析均空。", solution="")
add(1988, 2, 2, r"$\frac32$",
    "周期2，x=1的左右极限分别为1、2，狄利克雷收敛值为(1+2)/2。原答案PDF第2页误写2/3。", solution="")
add(1988, 5, 0, r"$y=(1-2x)e^x$",
    "齐次根1、2，特解-2xe^x；初值y(0)=1、y'(0)=-1。代回y''-3y'+2y=2e^x验证。",
    solution=r"公共切线给出 $y(0)=1,y'(0)=-1$。齐次通解为 $C_1e^x+C_2e^{2x}$，取特解 $-2xe^x$，所以 $y=C_1e^x+C_2e^{2x}-2xe^x$。由初值得 $C_1=1,C_2=0$，故 $y=(1-2x)e^x$。原解析末行的 $e^{2x}$ 为笔误。")

# The 1997 question collection contains overlapping/misordered glyphs.
# Repair only symbols whose positions and annual mathematical response agree.
add(1997, 1, 1, r"$\frac32$", "分子分母同除x，使用sin(x)/x与ln(1+x)/x极限；x cos(1/x)趋于0。",
    solution=r"同除 $x$ 得 $[3\sin x/x+x\cos(1/x)]/[(1+\cos x)\ln(1+x)/x]$，其极限为 $3/(2\cdot1)=3/2$。")
add(1997, 1, 2, r"$(-2,4)$", "逐项求导不改变收敛半径，平移x-1，开收敛区间由|x-1|<3确定。",
    question=r"设幂级数 $\sum_{n=0}^{\infty}a_nx^n$ 的收敛半径为3，则幂级数 $\sum_{n=1}^{\infty}na_n(x-1)^{n+1}$ 的收敛区间为 ____。",
    solution=r"令 $t=x-1$，原级数等于 $t^2\sum_{n\ge1}na_nt^{n-1}$。幂级数逐项求导不改变收敛半径，故 $|t|<3$，即 $-2<x<4$。")
add(1997, 1, 3, r"$x+y=e^{\pi/2}$", "用x=e^θ cosθ、y=e^θ sinθ求导，θ=π/2时斜率-1，切点(0,e^(π/2))。",
    question=r"对数螺线 $\rho=e^\theta$ 在点 $(\rho,\theta)=(e^{\pi/2},\pi/2)$ 处的切线的直角坐标方程为 ____。",
    solution=r"参数方程为 $x=e^\theta\cos\theta,y=e^\theta\sin\theta$。在 $\theta=\pi/2$ 时，切点为 $(0,e^{\pi/2})$，$dy/dx=(\sin\theta+\cos\theta)/(\cos\theta-\sin\theta)=-1$，故 $x+y=e^{\pi/2}$。")
add(1997, 1, 4, r"$-3$", "B非零且AB=0推出det(A)=0；det(A)=7(t+3)。",
    question=r"设 $A=\begin{pmatrix}1&2&-2\\4&t&3\\3&-1&1\end{pmatrix}$，$B$ 为3阶非零矩阵且 $AB=O$，则 $t=$ ____。",
    solution=r"由 $B\ne O$ 且 $AB=O$，齐次方程 $Ax=0$ 有非零解，故 $|A|=0$。计算 $|A|=7(t+3)$，得 $t=-3$。")
add(1997, 1, 5, r"$\frac25$", "不放回等概率抽样的第二个位置，其边缘黄球概率仍为20/50。",
    question=r"袋中有50个乒乓球，其中20个黄球、30个白球。两人依次随机地从袋中各取一球，取后不放回，则第二人取得黄球的概率是 ____。",
    solution=r"由全概率公式，$P(\text{第二球黄})=\frac{20}{50}\frac{19}{49}+\frac{30}{50}\frac{20}{49}=\frac25$。")
add(1997, 2, 1, "C", "沿y=x极限为1/2而沿坐标轴为0；两个偏导按定义均为0。",
    question=r"二元函数 $f(x,y)=\begin{cases}\frac{xy}{x^2+y^2},&(x,y)\ne(0,0),\\0,&(x,y)=(0,0)\end{cases}$ 在点 $(0,0)$ 处（ ）。",
    options=["连续，偏导数存在。", "连续，偏导数不存在。", "不连续，偏导数存在。", "不连续，偏导数不存在。"],
    solution=r"沿 $y=x$ 趋于原点时函数值为 $1/2$，沿坐标轴函数值为0，故不连续。由定义，$f_x(0,0)=f_y(0,0)=0$，所以选C。")
add(1997, 2, 2, "B", "严格递减给右端矩形小于积分；严格凸给积分小于梯形面积。",
    question=r"设在区间 $[a,b]$ 上 $f(x)>0,f'(x)<0,f''(x)>0$。令 $S_1=\int_a^b f(x)\,dx$，$S_2=f(b)(b-a)$，$S_3=\frac12[f(a)+f(b)](b-a)$，则（ ）。",
    options=[r"$S_1<S_2<S_3$",r"$S_2<S_1<S_3$",r"$S_3<S_1<S_2$",r"$S_2<S_3<S_1$"],
    solution=r"由严格递减性，$f(b)(b-a)<\int_a^bf(x)dx$；由严格凸性，曲线位于两端点连线下方，故积分小于梯形面积。因此 $S_2<S_1<S_3$，选B。")
add(1997, 2, 3, "A", "被积函数2π周期，整周期积分与起点无关；将t和t+π配对，积分严格为正。",
    question=r"设 $F(x)=\int_x^{x+2\pi}e^{\sin t}\sin t\,dt$，则 $F(x)$（ ）。",
    options=["为正常数。","为负常数。","恒为零。","不为常数。"],
    solution=r"被积函数以 $2\pi$ 为周期，故 $F(x)$ 为常数。且 $F(0)=\int_0^\pi\sin t(e^{\sin t}-e^{-\sin t})dt>0$，故选A。")
add(1997, 2, 4, "D", "三直线有唯一公共点等价于系数矩阵与增广矩阵同秩且秩为2。",
    question=r"设 $\alpha_1=(a_1,a_2,a_3)^T,\alpha_2=(b_1,b_2,b_3)^T,\alpha_3=(c_1,c_2,c_3)^T$，三条直线 $a_ix+b_iy+c_i=0$（$a_i^2+b_i^2\ne0,i=1,2,3$）交于一点的充要条件是（ ）。",
    options=[r"$\alpha_1,\alpha_2,\alpha_3$ 线性相关。",r"$\alpha_1,\alpha_2,\alpha_3$ 线性无关。",r"$r(\alpha_1,\alpha_2,\alpha_3)=r(\alpha_1,\alpha_2)$。",r"$\alpha_1,\alpha_2,\alpha_3$ 线性相关，且 $\alpha_1,\alpha_2$ 线性无关。"],
    solution=r"方程组有唯一解当且仅当 $r(\alpha_1,\alpha_2)=r(\alpha_1,\alpha_2,\alpha_3)=2$，这等价于D。")
add(1997, 2, 5, "D", "独立随机变量线性组合方差为9·4+4·2=44。",
    solution=r"由独立性，$D(3X-2Y)=9D(X)+4D(Y)=36+8=44$，选D。")
add(1997, 3, 0, r"(1) $\frac{1024\pi}{3}$；(2) $-2\pi$；(3) $x(t)=\frac{N}{1+(N/x_0-1)e^{-kNt}}$（$0<x_0<N$）。",
    "柱坐标积分；旋度(0,0,2)及顺时针方向；分离变量解logistic方程。端点初值x0=0或N分别为常值解。",
    solution=r"(1) 取柱坐标，$I=2\pi\int_0^8\int_0^{\sqrt{2z}}r^3drdz=1024\pi/3$。(2) 向量场旋度为 $(0,0,2)$，投影为单位圆盘；顺时针方向给出 $-2\pi$。(3) $x'=kx(N-x)$，分离变量并代入 $x(0)=x_0$ 得 $x=N/[1+(N/x_0-1)e^{-kNt}]$；若 $x_0=0$ 或 $N$，解分别为0或N。")
add(1997, 4, 0, r"(1) $a=-5,b=-2$；(2) $f(u)=C_1e^u+C_2e^{-u}$。",
    "切平面2x-4y-z-5=0，代入直线参数式令系数为0；复合函数拉普拉斯算子给e^(2x)f''(u)。",
    solution=r"(1) 切平面为 $2x-4y-z-5=0$。直线上 $y=-x-b,z=(1-a)x-ab-3$，代入得 $(a+5)x+(a+4)b-2=0$，故 $a=-5,b=-2$。(2) 令 $u=e^x\sin y$，有 $u_{xx}+u_{yy}=0$，$u_x^2+u_y^2=e^{2x}$，故 $f''(u)=f(u)$，从而 $f=C_1e^u+C_2e^{-u}$。")
add(1997, 5, 0, r"$\varphi'(x)=\frac{xf(x)-\int_0^xf(u)du}{x^2}$（$x\ne0$），$\varphi'(0)=A/2$，且在0处连续。",
    "积分换元及f(x)=Ax+o(x)；分别计算差商与导函数极限。",
    solution=r"由连续性和已知极限得 $f(0)=0$，$f(x)=Ax+o(x)$。对 $x\ne0$，换元得 $\varphi(x)=x^{-1}\int_0^xf(u)du$，求导得到所列公式。又 $\int_0^xf(u)du=Ax^2/2+o(x^2)$，所以 $\varphi'(0)=A/2$，且 $\lim_{x\to0}\varphi'(x)=A/2$，故连续。")
add(1997, 6, 0, r"(1) $a_n\downarrow1$；(2) 所给正项级数收敛。",
    "a_(n+1)≥1且a_(n+1)≤a_n；级数项≤a_n-a_(n+1)，望远镜比较。",
    solution=r"均值不等式给 $a_{n+1}\ge1$，且 $a_{n+1}-a_n=(1-a_n^2)/(2a_n)\le0$，故极限存在。令极限为L，得 $L=(L+1/L)/2$，所以L=1。又 $0\le a_n/a_{n+1}-1=(a_n-a_{n+1})/a_{n+1}\le a_n-a_{n+1}$，其部分和不超过 $a_1-1=1$，故级数收敛。")
add(1997, 7, 0, r"(1) $\{(1,1,2,3)^T/\sqrt{15},(-2,1,5,-3)^T/\sqrt{39}\}$；(2) $a=-3,b=0,\lambda=-1$，A不能相似于对角阵。",
    "Gram–Schmidt；代入Aξ=λξ；特征多项式(λ+1)^3而rank(A+E)=2。",
    solution=r"(1) 解空间维数为 $4-2=2$，$\alpha_1,\alpha_2$ 独立，正交化得到 $(1,1,2,3)^T/\sqrt{15}$ 与 $(-2,1,5,-3)^T/\sqrt{39}$。(2) 由第一分量得 $\lambda=-1$，再由其他分量得 $a=-3,b=0$。此时特征多项式为 $(\lambda+1)^3$，而 $r(A+E)=2$，特征空间维数只有1，故不可对角化。")
add(1997, 8, 0, r"B可逆，$AB^{-1}=E_{ij}$，其中 $E_{ij}$ 为交换第i、j行的初等矩阵。",
    "B=E_ij A，E_ij²=E，故B^-1=A^-1 E_ij。",
    solution=r"令 $E_{ij}$ 为交换第i、j行的初等矩阵，则 $B=E_{ij}A$。由于 $E_{ij}^2=E$ 且A可逆，B可逆，$B^{-1}=A^{-1}E_{ij}$，从而 $AB^{-1}=E_{ij}$。")
add(1997, 9, 0, r"$P(X=k)=\binom3k(\frac25)^k(\frac35)^{3-k}$（$k=0,1,2,3$）；$E(X)=6/5$。$F(x)$ 在 $x<0,0\le x<1,1\le x<2,2\le x<3,x\ge3$ 上依次为 $0,27/125,81/125,117/125,1$。",
    "独立Bernoulli事件和为Bin(3,2/5)，逐项累加CDF。",
    solution=r"三个独立红灯事件发生概率均为2/5，故 $X\sim B(3,2/5)$。各概率依次为 $27,54,36,8$ 除以125，累加得到所列分布函数，期望 $3\cdot2/5=6/5$。")
add(1997, 10, 0, r"矩估计 $\hat\theta_M=\frac{2\bar X-1}{1-\bar X}$；最大似然估计 $\hat\theta_L=-\frac{n}{\sum_{i=1}^n\ln X_i}-1$。",
    "积分得E(X)=(θ+1)/(θ+2)；对数似然导数n/(θ+1)+ΣlnXi=0，二阶导数<0。",
    solution=r"由 $E(X)=(\theta+1)\int_0^1x^{\theta+1}dx=(\theta+1)/(\theta+2)$，令其等于 $\bar X$ 得矩估计。对数似然 $\ell=n\ln(\theta+1)+\theta\sum\ln X_i$，令 $\ell'=0$ 得最大似然估计；$\ell''=-n/(\theta+1)^2<0$，保证极大值。")

add(2003, 2, 5, "B", "核对原编号①③；零空间包含关系反向对应秩，秩相等不决定零空间相等。",
    options=["①②","①③","②④","③④"])
add(2008, 1, 6, "B", "合集第67页图为双叶双曲面；补回图右侧被漏识别的D选项3。正惯性指数为1。",
    options=["0","1","2","3"], solution=r"实对称矩阵可经正交变换对角化。图示为双叶双曲面，其标准式一个平方项为正、两个为负，故正特征值个数为1，选B。")
add(2009, 1, 5, "A", "新基列向量在旧基(α1,α2/2,α3/3)中的坐标依次为(1,2,0)、(0,2,3)、(1,0,3)；原页跨页C标签漏识别。",
    question=r"设 $\alpha_1,\alpha_2,\alpha_3$ 是 $\mathbb R^3$ 的一组基，则由基 $\alpha_1,\frac12\alpha_2,\frac13\alpha_3$ 到基 $\alpha_1+\alpha_2,\alpha_2+\alpha_3,\alpha_3+\alpha_1$ 的过渡矩阵为（ ）。",
    options=[r"$\begin{pmatrix}1&0&1\\2&2&0\\0&3&3\end{pmatrix}$",r"$\begin{pmatrix}1&2&0\\0&2&3\\1&0&3\end{pmatrix}$",r"$\begin{pmatrix}1/2&1/4&-1/6\\-1/2&1/4&1/6\\1/2&-1/4&1/6\end{pmatrix}$",r"$\begin{pmatrix}1/2&-1/2&1/2\\1/4&1/4&-1/4\\-1/6&1/6&1/6\end{pmatrix}$"])
add(2013, 1, 2, "A", "梯度在(0,1,-1)为(1,-1,1)，得到x-y+z=-2；原页A标签位于公式span。",
    question=r"曲面 $x^2+\cos(xy)+yz+x=0$ 在点 $(0,1,-1)$ 处的切平面方程为（ ）。",
    options=[r"$x-y+z=-2$",r"$x+y+z=0$",r"$x-2y+z=-3$",r"$x-y-z=0$"])
add(2013, 1, 3, "C", "合集第84页A为3/4，恢复空格标签；正弦级数对应奇延拓再作2周期延拓。",
    options=[r"$3/4$",r"$1/4$",r"$-1/4$",r"$-3/4$"],
    solution=r"正弦级数代表 $f$ 在 $(-1,1)$ 上的奇延拓并作2周期延拓。因此 $S(-9/4)=S(-1/4)=-f(1/4)=-1/4$，选C。")
add(2013, 2, 14, r"$1-e^{-1}$", "指数分布无记忆性，或直接以[e^-a-e^-(a+1)]/e^-a计算。",
    solution=r"$P(Y\le a+1\mid Y>a)=P(a<Y\le a+1)/P(Y>a)=[e^{-a}-e^{-(a+1)}]/e^{-a}=1-e^{-1}$。")
add(2020, 3, 22, r"$F_{X_1,Y}(x,y)=\frac12\Phi(\min\{x,y\})+\frac12\Phi(x)\Phi(y)$；$Y\sim N(0,1)$。",
    "按X3=1或0应用全概率公式，分布函数令x趋于正无穷验证边缘分布。",
    solution=r"当 $X_3=1$ 时，$Y=X_1$，故联合概率为 $\Phi(\min\{x,y\})$；当 $X_3=0$ 时，$Y=X_2$ 与 $X_1$ 独立，联合概率为 $\Phi(x)\Phi(y)$。两种情形概率均为1/2，相加得到所列分布函数。令 $x\to+\infty$，得 $F_Y(y)=\Phi(y)$，所以Y为标准正态变量。")
add(2020, 3, 23, r"$P(T>t)=e^{-(t/\theta)^m}$；$P(T>s+t\mid T>s)=e^{-[(s+t)^m-s^m]/\theta^m}$；$\hat\theta=(\frac1n\sum_{i=1}^nt_i^m)^{1/m}$。",
    "存活函数及嵌套事件条件概率；对数似然对θ求导，θ^m=Σt_i^m/n。",
    solution=r"(I) 由 $1-F(t)$ 得存活概率。因 $T>s+t$ 蕴含 $T>s$，条件概率为两个存活概率之比。(II) 密度为 $m t^{m-1}\theta^{-m}e^{-t^m/\theta^m}$。对数似然中与θ有关的项为 $-nm\ln\theta-\theta^{-m}\sum t_i^m$，令其导数为0，得 $\theta^m=\sum t_i^m/n$，从而得到估计值。")

add(2022, 1, 1, "B", "f(x)=ln(x)[1+o(1)]给lim f=0，不约束f(1)或导数。已与原页选项核对。",
    solution=r"由 $f(x)/\ln x\to1$ 且 $\ln x\to0$，得 $\lim_{x\to1}f(x)=0$，故B成立。该条件不约束 $f(1)$，也不能保证导数存在或导数极限存在。")
add(2022, 1, 2, "B", "2026-10-19用户人工修正本地原稿的重复选项，采用用户已修改的C/D选项。由xz_x+yz_y=2xyf(y/x)得f(u)=ln(u)/2，故f(1)=0、f'(1)=1/2，只有B成立。保留原稿错误的历史依据，不声明已恢复官方排版。",
    question=r"设 $f(u)$ 可导，$z=xyf(y/x)$，若 $xz_x+yz_y=xy(\ln y-\ln x)$，则下列哪些选项成立？",
    options=[r"$f(1)=1/2,\ f'(1)=0$",r"$f(1)=0,\ f'(1)=1/2$",r"$f(1)=1/2,\ f'(1)=1$",r"$f(1)=0,\ f'(1)=1$"],
    solution=r"计算得 $xz_x+yz_y=2xyf(y/x)$，所以 $f(u)=\frac12\ln u$。于是 $f(1)=0,f'(1)=1/2$。B成立。")
add(2022, 1, 3, "D", "取x_n=(-1)^nπ/4验证D；sin在[-π/2,π/2]上有连续反函数，故C不成立。原材料此题解析为空。", solution="")
add(2022, 1, 4, "A", "0<x<1时x/2<ln(1+x)<x；再用1+sin x≤2、1+cos x≥1比较被积函数，得I1<I2<I3。原材料解析空，C/D虽重复但均非正确选项。", solution="")
add(2022, 1, 5, "A", "三个不同特征值保证三个独立特征向量；单位矩阵说明此条件非必要。",
    solution=r"3阶矩阵有3个不同特征值时必有3个线性无关特征向量，从而可对角化。单位矩阵可对角化而只有一个不同特征值，故该条件非必要，选A。")
add(2022, 1, 6, "C", "设共同零空间为K；两个C项分块方程的解空间均为K×K。按原页修复分块矩阵OCR。",
    question=r"设矩阵 $A,B$ 均为 $n$ 阶方阵，若 $Ax=0$ 与 $Bx=0$ 同解，则（ ）。",
    options=[r"$\begin{pmatrix}A&O\\E&B\end{pmatrix}x=0$ 仅有零解。",r"$\begin{pmatrix}AB&B\\O&A\end{pmatrix}x=0$ 仅有零解。",r"$\begin{pmatrix}A&B\\O&B\end{pmatrix}x=0$ 与 $\begin{pmatrix}B&A\\O&A\end{pmatrix}x=0$ 同解。",r"$\begin{pmatrix}AB&B\\O&A\end{pmatrix}x=0$ 与 $\begin{pmatrix}BA&A\\O&B\end{pmatrix}x=0$ 同解。"],
    solution=r"记 $K=\ker A=\ker B$，将未知向量分为 $(u,v)$。C中第一个方程先给 $v\in K$，再给 $Au=0$，所以解为 $K\times K$；第二个方程同理，故选C。")
add(2022, 1, 7, "C", "两组的3阶行列式分别为(λ-1)²(λ+2)与(λ-1)²(λ+1)²。λ=1时均为同一条直线，其余奇异值-1、-2不能等价；已用符号行列式核验。",
    solution=r"两组三阶行列式分别为 $(\lambda-1)^2(\lambda+2)$ 与 $(\lambda-1)^2(\lambda+1)^2$。除 $1,-1,-2$ 外均张成三维空间；$\lambda=1$ 时四向量相同，也等价；$\lambda=-1$ 或 $-2$ 时两组秩不同。因此排除 $-1,-2$，选C。")
add(2022, 1, 8, "B", "Var(X)=3/4，Var(Y)=2，Var(2X-Y+1)=4·3/4+2-4(-1)=9。",
    solution=r"$D(X)=(3-0)^2/12=3/4$，$D(Y)=2$。故 $D(2X-Y+1)=4D(X)+D(Y)-4\operatorname{Cov}(X,Y)=3+2+4=9$，选B。")
add(2022, 1, 9, "C", "样本均值方差(μ2-μ1²)/n，直接用切比雪夫不等式；原材料最终答案与解析均空。", solution="")
add(2022, 1, 10, "D", "E(Y|X)=X，Var(Y|X)=1；Var(Y)=2，Cov(X,Y)=1，故相关系数1/sqrt(2)。原解析空。", solution="")
add(2022, 2, 11, "4", "最大方向导数为梯度模；在(0,1)梯度(0,4)。",
    solution=r"$\nabla f=(2x,4y)$，在 $(0,1)$ 为 $(0,4)$，最大方向导数等于其模4。")
add(2022, 2, 12, "4", "原题上限为e²；原函数2sqrt(x)ln(x)-4sqrt(x)，代入两端得4。",
    solution=r"$\int \ln x/\sqrt{x}\,dx=2\sqrt{x}\ln x-4\sqrt{x}+C$，代入1与 $e^2$ 得4。")
add(2022, 2, 13, r"$4/e^2$", "对所有非负x,y作最优统一上界；令s=x+y，x²+y²≤s²，max s²e^-s=4/e²，在(2,0)达到。明确原题隐含的全称量词。",
    question=r"使不等式 $x^2+y^2\le ke^{x+y}$ 对任意 $x\ge0,y\ge0$ 都成立的常数 $k$ 的最小值为 ____。",
    solution=r"令 $s=x+y\ge0$，则 $x^2+y^2\le s^2$，所以 $(x^2+y^2)e^{-x-y}\le s^2e^{-s}\le4e^{-2}$。在 $(x,y)=(2,0)$ 或 $(0,2)$ 达到等号，因此最小值为 $4/e^2$。")
add(2022, 2, 14, "-1", "原题e^(-n-x)与所声明的收敛区间矛盾；年度解析明确使用e^(-nx)，按该配套解析校正。比值极限e^(-1-x)，x=-1时通项不趋于0。",
    question=r"级数 $\sum_{n=1}^{\infty}\frac{n!}{n^n}e^{-nx}$ 的收敛域为 $(a,+\infty)$，则 $a=$ ____。",
    solution=r"令 $u_n=n!n^{-n}e^{-nx}$，则 $u_{n+1}/u_n=(n/(n+1))^ne^{-x}\to e^{-1-x}$。故 $x>-1$ 收敛，$x<-1$ 发散；在 $x=-1$ 时由斯特林公式 $u_n\sim\sqrt{2\pi n}$，通项不趋于0，故 $a=-1$。")
add(2022, 2, 15, r"$(A-2E)^{-1}A$", "将原等式左乘A-E得到(A-2E)B=(A-E)A，右端可逆保证A-2E可逆，然后相减。",
    solution=r"左乘 $A-E$ 得 $(A-2E)B=(A-E)A$。右端可逆，所以 $A-2E$ 可逆。又 $(A-2E)(B-A)=A$，故 $B-A=(A-2E)^{-1}A$。")
add(2022, 2, 16, r"$5/8$", "BC独立给P(B∪C)=5/9；A与两事件互斥，分母为1/3+5/9=8/9。",
    solution=r"$P(B\cup C)=1/3+1/3-1/9=5/9$。因A与 $B\cup C$ 互斥，$P(A\cup B\cup C)=1/3+5/9=8/9$，故所求条件概率为5/8。")
add(2022, 3, 17, r"$y=2x$", "积分因子e^(sqrt(x))，解y=2x+e^(1-sqrt(x))，两者差趋于0。",
    solution=r"积分因子为 $e^{\sqrt{x}}$，方程解为 $y=2x+Ce^{-\sqrt{x}}$。由 $y(1)=3$ 得C=e。因此 $y-2x=e^{1-\sqrt{x}}\to0$，渐近线为 $y=2x$。")
add(2022, 3, 18, r"$2\pi-2$", "根据原页的上下限次序及原解析补回残损不等号；极坐标将右四分之一圆盘与左三角形分开，积分分别为π-2、π。",
    question=r"设 $D=\{(x,y)\mid y-2\le x\le\sqrt{4-y^2},\ 0\le y\le2\}$，求二重积分 $I=\iint_D\frac{(x-y)^2}{x^2+y^2}\,dxdy$。",
    solution=r"取极坐标，被积函数为 $1-\sin2\theta$。右侧四分之一圆盘上 $0\le\theta\le\pi/2,0\le r\le2$，积分为 $2\int_0^{\pi/2}(1-\sin2\theta)d\theta=\pi-2$。左侧三角形上 $\pi/2\le\theta\le\pi,0\le r\le2/(\sin\theta-\cos\theta)$，径向积分后恒为2，故积分为π。相加得 $2\pi-2$。")
add(2022, 3, 19, r"$\pi/8$", "原页第一个微分项为dx（OCR为dz）；旋度(2xz,0,2y²-z²)，在第一卦限单位球面按上侧投影得到3(x²+y²)-1。原解析未给出推导，solution保持空。",
    question=r"设 $\Sigma$ 为球面 $x^2+y^2+z^2=1$ 在 $x,y,z\ge0$ 部分的上侧，其边界L的方向与所取侧符合右手法则。求 $\oint_L(yz^2-\cos z)\,dx+2xy^2\,dy+(2xyz+x\sin z)\,dz$。", solution="")
add(2022, 3, 20, "所述充要关系成立。", "充分性由凸性与对称点平均；必要性在[a,b]=[x-h,x+h]处作二阶Taylor展开，平均值与f(x)之差=f''(x)h²/6+o(h²)。补充a<b避免分母为0。",
    question=r"设 $f$ 在 $\mathbb R$ 上有二阶连续导数。证明：对所有 $x$ 有 $f''(x)\ge0$ 的充要条件是，对任意 $a<b$，有 $f((a+b)/2)\le\frac1{b-a}\int_a^b f(x)\,dx$。",
    solution=r"若 $f''\ge0$，f为凸函数，故 $f((a+b)/2)\le[f(x)+f(a+b-x)]/2$，在[a,b]上积分即得结论。反之，取 $a=x-h,b=x+h$。二阶Taylor展开给 $\frac1{2h}\int_{x-h}^{x+h}f(t)dt-f(x)=f''(x)h^2/6+o(h^2)\ge0$。除以 $h^2$ 并令h趋于0，得到 $f''(x)\ge0$。")
add(2022, 3, 21, r"$A=\begin{pmatrix}1&2&3\\2&4&6\\3&6&9\end{pmatrix}$；可取 $Q=\begin{pmatrix}1/\sqrt{14}&2/\sqrt5&3/\sqrt{70}\\2/\sqrt{14}&-1/\sqrt5&6/\sqrt{70}\\3/\sqrt{14}&0&-5/\sqrt{70}\end{pmatrix}$，标准形 $14y_1^2$；零点集为 $x_1+2x_2+3x_3=0$。",
    "A=vv^T，v=(1,2,3)^T；显式验证Q^TQ=E及Q^TAQ=diag(14,0,0)。",
    solution=r"$f=(x_1+2x_2+3x_3)^2$，所以A为所列矩阵。取Q的三列为 $(1,2,3)^T/\sqrt{14}$、$(2,-1,0)^T/\sqrt5$、$(3,6,-5)^T/\sqrt{70}$，它们标准正交，且对应特征值14、0、0，因此标准形为 $14y_1^2$。$f=0$ 等价于 $x_1+2x_2+3x_3=0$，亦可参数化为 $(-2s-3t,s,t)$。")
add(2022, 3, 22, r"$\hat\theta=\frac{\sum_{i=1}^nX_i+\frac12\sum_{j=1}^mY_j}{n+m}$，$D(\hat\theta)=\frac{\theta^2}{n+m}$。",
    "对数似然=-(n+m)lnθ-[ΣXi+ΣYj/2]/θ+常数；独立性与指数分布方差求估计量方差。移除下一年度封面的“绝密★启用前”。",
    solution=r"记 $S=\sum X_i+\frac12\sum Y_j$。与θ有关的对数似然为 $-(n+m)\ln\theta-S/\theta$，其极大值点为 $\hat\theta=S/(n+m)$。由独立性，$D(S)=n\theta^2+\frac14m(2\theta)^2=(n+m)\theta^2$，故 $D(\hat\theta)=\theta^2/(n+m)$。")
