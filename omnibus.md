# Foundations of Arithmetic and Algebra

An Omnibus of Operations, Laws, and Axioms, in the Axiomatic Style of Landau

In the manner of Landau's Grundlagen der Analysis*: every* Definition is a stipulation, every Satz (Theorem) is proved from what precedes it and nothing else, and nothing is asserted without a Beweis (Proof). Numbering is continuous within each chapter. Where Landau builds only N, Z, Q, R concretely, this omnibus first isolates the abstract laws those systems happen to satisfy, states them once and for all for an arbitrary set with arbitrary operations, and then exhibits N, Z, Q, R as particular instances. This is the modern (post-Landau) move -- universal algebra -- and it is what lets "commutative," "associative," "left identity," and so on be stated exactly once instead of four times.

A one-line remark of orientation opens each chapter; everything after it is formal.

## Chapter 0 -- Sets, Relations, Operations, and Functions

Note. Everything downstream -- laws of +, times, order, exponentiation, floor -- is a special case of one of three primitive notions: a relation (of which order and equality are instances), an operation (of which +, times are instances), and a function (of which every operation, being a function \(S^n \to S\), is itself an instance). This chapter treats all three in full generality before Chapter 1 restricts attention to a single binary operation.

### 0.1 Sets and Cartesian Products

Definition 0.1 (Set, element). We take set and membership (in) as primitive. \(A\) is a subset of \(B\) iff for all \(x\), \(x \in A\) implies \(x \in B\). \(A=B\) iff \(A\) is a subset of \(B\) and \(B\) is a subset of \(A\) (extensionality).

Definition 0.2 (Boolean operations on sets). \(A \cup B := \{x: x \in A \text{ or } x \in B\}\); \(A \cap B := \{x: x \in A \text{ and } x \in B\}\); \(A \setminus B := \{x \in A: x \notin B\}\); for \(A\) a subset of a fixed universe \(U\), \(A^c := U \setminus A\).

Satz 0.3 (De Morgan's laws). \((A \cup B)^c = A^c \cap B^c\) and \((A \cap B)^c = A^c \cup B^c\).

Beweis. \(x \in (A \cup B)^c\) iff not \((x \in A \text{ or } x \in B)\) iff not \((x \in A)\) and not \((x \in B)\) iff \(x \in A^c \cap B^c\), by the propositional-logic law \(\neg(P \lor Q) \leftrightarrow \neg P \land \neg Q\); the second identity is the dual, using \(\neg(P \land Q) \leftrightarrow \neg P \lor \neg Q\). \(\blacksquare\)

Definition 0.4 (Ordered pair, Cartesian product). For sets \(A,B\): \(A \times B := \{(a,b): a \in A, b \in B\}\), with \((a,b)=(a',b')\) iff \(a=a'\) and \(b=b'\). For \(n \geq 1\) and sets \(S_1,\dots,S_n\), \(S_1 \times \cdots \times S_n\) is defined analogously via \(n\)-tuples \((x_1,\dots,x_n)\); write \(S^n:=S \times \cdots \times S\) (\(n\) factors), and \(S^0\) is, by convention, a fixed one-element set (the empty tuple).

### 0.2 n-ary Relations and n-ary Operations

Definition 0.5 (n-ary relation). An \(n\)-ary relation on \(S\) is a subset \(R \subseteq S^n\). The case \(n=2\) is a binary relation, written \(x \mathrel{R} y\) for \((x,y) \in R\); \(n=1\) is a unary relation (a subset, i.e. a predicate); \(n=0\) is a nullary relation, i.e. one of the two truth values (since \(S^0\) has one element).

Definition 0.6 (n-ary operation). An \(n\)-ary operation on \(S\) is a function \(\omega : S^n \to S\).

- \(n=0\) (nullary operation): a function \(S^0 \to S\) is, in effect, a single distinguished element \(c \in S\) (a constant). This is the formal home of "the identity element" and "the zero element": each is really a nullary operation, singling out one point of \(S\), and Chapter 1's "identity" and "absorbing element" laws are laws relating that nullary operation to a binary one.
- \(n=1\) (unary operation): a function \(S \to S\) (e.g. negation \(x \mapsto -x\), inversion \(x \mapsto x^{-1}\), complementation).
- \(n=2\) (binary operation): a function \(*:S \times S \to S\); write \(x*y\) for \(*(x,y)\). This is the case Chapters 1-9 study almost exclusively, and (per Def. 0.6's remark on closure) the fact that the codomain is \(S\) itself is what "closure" means -- it is not a separately verified axiom but part of what it is to be an operation on \(S\).
- \(n \geq 3\): ternary, quaternary, ..., generally \(n\)-ary operations; not otherwise used in this omnibus.

### 0.3 Named Properties of a Binary Relation

Note. These sixteen properties are the alphabet from which every "kind of order," "kind of equivalence," and (in Chapter 4) every ordered algebraic structure is spelled. Fix a binary relation \(R\) on \(S\); write \(xRy\).

Definition 0.7. \(R\) is:

| Name | Defining condition |
|---|---|
| reflexive | for all \(x\): \(xRx\) |
| irreflexive | for all \(x\): not \((xRx)\) |
| symmetric | for all \(x,y\): \(xRy\) implies \(yRx\) |
| antisymmetric | for all \(x,y\): \((xRy \text{ and } yRx)\) implies \(x=y\) |
| asymmetric | for all \(x,y\): \(xRy\) implies not \((yRx)\) |
| transitive | for all \(x,y,z\): \((xRy \text{ and } yRz)\) implies \(xRz\) |
| total (connex) | for all \(x,y\): \(xRy\) or \(yRx\) |
| trichotomous | for all \(x,y\): exactly one of \(xRy\), \(x=y\), \(yRx\) holds |
| left-Euclidean | for all \(x,y,z\): \((yRx \text{ and } zRx)\) implies \(yRz\) |
| right-Euclidean | for all \(x,y,z\): \((xRy \text{ and } xRz)\) implies \(yRz\) |
| dense | for all \(x,y\): \(xRy\) implies there exists \(z\) with \(xRz\) and \(zRy\) |
| well-founded | every nonempty \(T \subseteq S\) has an \(R\)-minimal element: there exists \(m \in T\) such that for all \(t \in T\), not \((tRm)\) |

Satz 0.8 (Interrelations among these properties).

(i) \(R\) asymmetric iff \(R\) irreflexive and \(R\) antisymmetric.

(ii) \(R\) irreflexive and transitive implies \(R\) asymmetric.

(iii) \(R\) reflexive and transitive and right-Euclidean implies \(R\) symmetric.

(iv) \(R\) trichotomous implies \(R\) irreflexive and asymmetric.

Beweis.

(i) (implies) Suppose \(R\) asymmetric. If \(xRx\) held, asymmetry with \(y=x\) gives not \((xRx)\), contradiction; so \(R\) is irreflexive. If \(xRy\) and \(yRx\), asymmetry forbids this whenever \(x \neq y\); hence \((xRy \land yRx) \to x=y\), so \(R\) is antisymmetric.

(is implied by) Suppose \(R\) irreflexive and antisymmetric. Suppose \(xRy\); if \(yRx\) also held, antisymmetry gives \(x=y\), and substituting into \(xRy\) gives \(xRx\), contradicting irreflexivity. So not \((yRx)\): \(R\) is asymmetric.

(ii) Suppose \(xRy\) and \(yRx\). Transitivity gives \(xRx\), contradicting irreflexivity. Thus, if \(xRy\), \(yRx\) cannot hold, so \(R\) is asymmetric.

(iii) Suppose \(xRy\). By reflexivity, \(xRx\). Right-Euclidean says \((xRy \land xRz) \to yRz\); take \(z=x\). From \(xRy\) and \(xRx\), conclude \(yRx\). Thus \(R\) is symmetric.

(iv) Immediate: trichotomy's "exactly one of \(xRy,x=y,yRx\)" forbids \(xRx\) (when \(y=x\)) and forbids \(xRy\) and \(yRx\) simultaneously. \(\blacksquare\)

### 0.4 Named Composite Relation Types

Definition 0.9 (Preorder, partial order, total order, equivalence, well-order). \(R\) on \(S\) is a:

- preorder (or quasiorder) iff reflexive and transitive;
- partial order iff reflexive and antisymmetric and transitive (i.e. a preorder that is also antisymmetric); a set with a partial order is a poset;
- strict partial order iff irreflexive and transitive (automatically asymmetric, Satz 0.8(ii));
- total (linear) order iff a partial order that is also total;
- strict total (linear) order iff a strict partial order that is also trichotomous -- this is exactly Def. 4.1 below, now seen as an instance of the general scheme;
- equivalence relation iff reflexive and symmetric and transitive;
- well-order iff a total order that is well-founded, i.e. every nonempty subset has a least element.

Satz 0.10 (Strict/non-strict correspondence). Let \(\leq\) be a partial order on \(S\). Define \(x<y\) iff \(x \leq y\) and \(x \neq y\). Then \(<\) is a strict partial order on \(S\). Conversely, let \(<\) be a strict partial order on \(S\); define \(x \leq y\) iff \(x<y\) or \(x=y\). Then \(\leq\) is a partial order. These two constructions are mutually inverse.

Beweis. \((\leq \rightsquigarrow <)\): Irreflexivity of \(<\) is immediate (\(x<x\) would require \(x \neq x\), false). Transitivity: if \(x<y\) and \(y<z\), then \(x \leq y\), \(y \leq z\) give \(x \leq z\). If \(x=z\), then \(y \leq z=x\), and with \(x \leq y\), antisymmetry gives \(x=y\), contradicting \(x<y\)'s requirement \(x \neq y\). Thus \(x \neq z\), giving \(x<z\).

\((< \rightsquigarrow \leq)\): Reflexivity is the \(x=y\) disjunct. Antisymmetry: if \(x \leq y\) and \(y \leq x\), then either some equality already gives \(x=y\), or \(x<y<x\), contradicting asymmetry of the strict partial order. Transitivity follows by case-splitting each \(\leq\) into its two disjuncts and using transitivity of \(<\) or equality cases trivially.

Mutual inverse follows by unwinding the definitions. \(\blacksquare\)

Satz 0.11 (Fundamental theorem of equivalence relations). Let \(\sim\) be an equivalence relation on \(S\). For \(x \in S\), define the equivalence class \([x] := \{y \in S: y \sim x\}\). Then:

(i) \(x \in [x]\) for every \(x\) (so the classes cover \(S\) and are nonempty);

(ii) for all \(x,y\): \([x] \cap [y] \neq \emptyset\) iff \([x]=[y]\).

Consequently \(\{[x]: x \in S\}\) is a partition of \(S\). Conversely, every partition \(\mathcal P\) of \(S\) arises this way from a unique equivalence relation, namely \(x \sim y\) iff \(x,y\) lie in the same block of \(\mathcal P\).

Beweis. (i) By reflexivity, \(x \sim x\), so \(x \in [x]\).

(ii) If \([x]=[y]\), then \(x \in [x]=[y]\), so the intersection is nonempty. Conversely, suppose \(z \in [x] \cap [y]\). Then \(z \sim x\) and \(z \sim y\). By symmetry \(x \sim z\), and by transitivity \(x \sim y\). If \(w \in [x]\), then \(w \sim x\) and \(x \sim y\), so \(w \sim y\), hence \(w \in [y]\). Thus \([x] \subseteq [y]\), and symmetrically \([y] \subseteq [x]\). Hence \([x]=[y]\). The partition and converse statements follow directly. \(\blacksquare\)

## Chapter 0A -- Functions

Note. A function is, by Def. 0.13 below, a special kind of relation; everything about relations already established (Ch. 0.3-0.4) is therefore available, but functions earn their own vocabulary because of how they interact with sets (images, preimages) and with each other (composition).

### 0A.1 Domain, Codomain, Graph, Fibers

Definition 0.13 (Function, domain, codomain, graph). A function \(f:A \to B\) is a relation \(f \subseteq A \times B\) such that each \(a \in A\) is related to exactly one \(b \in B\). \(A\) is the domain, \(B\) the codomain; write \(f(a)=b\) for \((a,b) \in f\). The set \(f \subseteq A \times B\) itself is called the graph of \(f\) -- under this standard, modern convention a function simply is its graph.

Definition 0.14 (Image of a set, direct image). For \(f:A \to B\) and \(X \subseteq A\), \(f(X):=\{f(x): x \in X\}\). \(f(A)\), the image of the whole domain, is called the range or image of \(f\).

Definition 0.15 (Preimage / inverse image of a set). For \(f:A \to B\) and \(Y \subseteq B\), \(f^{-1}(Y):=\{x \in A: f(x) \in Y\}\). This notation is defined for any \(f\) and any subset \(Y\), whether or not \(f\) is invertible.

Definition 0.16 (Fiber). For \(b \in B\), the fiber of \(f\) over \(b\) is \(f^{-1}(\{b\})\).

Satz 0.17 (Injective/surjective/bijective, restated via fibers). \(f:A \to B\) is:

(i) injective iff every fiber has at most one element;

(ii) surjective iff every fiber is nonempty;

(iii) bijective iff every fiber has exactly one element.

Beweis. (i) \(f\) injective means \(f(a)=f(a')\) implies \(a=a'\); this is exactly the assertion that a fiber cannot contain two distinct elements. (ii) Surjective means every \(b \in B\) has some \(a\) with \(f(a)=b\), i.e. every fiber is nonempty. (iii) is the conjunction of (i) and (ii). \(\blacksquare\)

### 0A.2 Restriction, Extension, Inverse Function

Definition 0.18 (Restriction). For \(f:A \to B\) and \(X \subseteq A\), the restriction \(f|_X : X \to B\) is defined by \(f|_X(x):=f(x)\) for \(x \in X\); formally \(f|_X = f \cap (X \times B)\).

Definition 0.19 (Extension). \(g:A' \to B\) is an extension of \(f:A \to B\) iff \(A \subseteq A'\) and \(g|_A=f\).

Definition 0.20 (Inverse function). If \(f:A \to B\) is bijective, the inverse function \(f^{-1}:B \to A\) is defined by sending \(b\) to the unique \(a\) with \(f(a)=b\) (existence and uniqueness by Satz 0.17(iii)).

Remark 0.21 (Notational clash -- flagged explicitly). The symbol \(f^{-1}\) is used for two different objects: (a) the inverse function, defined only when \(f\) is bijective; (b) applied to a set \(Y \subseteq B\), the preimage \(f^{-1}(Y)\), defined for every function \(f\). When \(f\) is bijective these agree in the natural sense, but the preimage notation must not be read as asserting \(f\) has an inverse function.

Satz 0.22 (Consistency of the two \(f^{-1}\)'s). If \(f:A \to B\) is bijective with inverse function \(f^{-1}\), then for every \(Y \subseteq B\), the preimage of \(Y\) under \(f\) equals the image of \(Y\) under the inverse function.

Beweis. \(x \in f^{-1}(Y)\) (preimage sense) iff \(f(x) \in Y\) iff \(x=f^{-1}(f(x))\) with \(f(x) \in Y\), which is exactly membership in the image of \(Y\) under the inverse function. \(\blacksquare\)

### 0A.3 Composition

Definition 0.23 (Composition). For \(f:A \to B\) and \(g:B \to C\), the composite \(g \circ f:A \to C\) is defined by \((g \circ f)(x):=g(f(x))\).

Satz 0.24 (Inverse function undoes \(f\) -- two-sided). If \(f:A \to B\) is bijective with inverse \(f^{-1}\), then \(f^{-1} \circ f = \operatorname{id}_A\) and \(f \circ f^{-1} = \operatorname{id}_B\), where \(\operatorname{id}_S:S \to S\), \(\operatorname{id}_S(x):=x\), is the identity function.

Beweis. \((f^{-1}\circ f)(a)=f^{-1}(f(a))=a\) by uniqueness of the preimage of \(f(a)\). Symmetrically \(f(f^{-1}(b))=b\). \(\blacksquare\)

Satz 0.25 (Composition is associative). For \(f:A \to B\), \(g:B \to C\), \(h:C \to D\): \((h \circ g)\circ f = h \circ (g \circ f)\).

Beweis. For \(x \in A\), both sides equal \(h(g(f(x)))\). \(\blacksquare\)

Satz 0.26 (The monoid of self-maps). For any set \(S\), let \(\operatorname{Fun}(S,S):=\{f:S \to S\}\). Then \((\operatorname{Fun}(S,S),\circ)\) is a monoid with identity \(\operatorname{id}_S\).

Beweis. Composition of self-maps is a self-map, associativity is Satz 0.25, and \(\operatorname{id}_S\) is a two-sided identity. \(\blacksquare\)

Satz 0.27 (Bijections form a group; inverse function = group inverse under \(\circ\)). The set \(\operatorname{Sym}(S):=\{f \in \operatorname{Fun}(S,S): f \text{ bijective}\}\) is a group under \(\circ\), and for \(f \in \operatorname{Sym}(S)\), the group inverse of \(f\) is exactly the inverse function \(f^{-1}\).

Beweis. Closure follows because a composite of bijections is bijective. Associativity and identity are inherited from Satz 0.26. Satz 0.24 gives the two-sided inverse. \(\blacksquare\)

Satz 0.28 (Left/right invertibility \(\leftrightarrow\) injective/surjective). Let \(f:A \to B\) with \(A \neq \emptyset\).

(i) \(f\) has a left inverse under \(\circ\) iff \(f\) is injective.

(ii) \(f\) has a right inverse under \(\circ\) iff \(f\) is surjective. This direction of (ii) uses the Axiom of Choice to select, for each \(b \in B\), a point of the nonempty fiber \(f^{-1}(\{b\})\); the converse direction does not.

Beweis. (i) If \(g\circ f=\operatorname{id}_A\), then \(f(a)=f(a')\) implies \(a=g(f(a))=g(f(a'))=a'\), so \(f\) is injective. Conversely, if \(f\) is injective, choose \(a_0 \in A\), and define \(g:B \to A\) by \(g(b)\) as the unique preimage of \(b\) when \(b \in f(A)\), otherwise \(g(b):=a_0\). Then \(g\circ f=\operatorname{id}_A\). (ii) If \(f\circ g=\operatorname{id}_B\), then every \(b\) is \(f(g(b))\), so \(f\) is surjective. Conversely choose \(g(b)\) from each nonempty fiber. \(\blacksquare\)

### 0A.4 Algebra of Functions (Pointwise Operations)

Definition 0.29 (Pointwise operation on function spaces). Let \((S,*)\) be a set with a binary operation, and \(X\) any set. On \(\operatorname{Fun}(X,S)\), define \((f \circledast g)(x):=f(x)*g(x)\).

Satz 0.30 (Transfer of laws to function spaces). \(\operatorname{Fun}(X,S)\) inherits, pointwise, every property of Chapter 1 that \((S,*)\) has: if \(*\) is associative, so is \(\circledast\); if \(*\) is commutative, so is \(\circledast\); if \((S,*)\) has identity \(e\), then \(\operatorname{Fun}(X,S)\) has identity the constant function \(\bar e(x):=e\); if every element of \(S\) has a \(*\)-inverse, every \(f\) has a pointwise inverse. Consequently: if \((S,*)\) is a monoid (resp. group, resp. abelian group), so is \((\operatorname{Fun}(X,S),\circledast)\).

Beweis. Each clause is verified pointwise at arbitrary \(x \in X\), reducing directly to the corresponding law in \(S\). \(\blacksquare\)

Remark 0.31 (Second notational clash). For \(f:X \to S\) with \((S,+,\times)\) a ring, both a compositional structure and a pointwise algebraic structure may coexist on the same underlying set of functions, and they do not agree: the pointwise additive inverse \(-f\) is not the compositional inverse of \(f\), and pointwise multiplication \(fg\) is not composition \(f\circ g\). Keep the operation in view whenever \(f^{-1}\), \(fg\), or \(f+g\) is written for a function.

### 0A.5 Functions and Set Operations

Note. Images distribute over unions but only sub-distribute over intersections; preimages distribute over everything -- this asymmetry is the single most useful fact in this section and is worth remembering as a slogan: "preimages are perfectly well-behaved; images are not."

Satz 0.32 (Image and union/intersection/difference; arbitrary families). Let \(f:A \to B\), \(X,Y \subseteq A\), and \((X_i)_{i\in I}\) a family of subsets of \(A\).

(i) \(f(X \cup Y)=f(X)\cup f(Y)\); more generally \(f(\bigcup_i X_i)=\bigcup_i f(X_i)\).

(ii) \(f(X \cap Y)\subseteq f(X)\cap f(Y)\); more generally \(f(\bigcap_i X_i)\subseteq \bigcap_i f(X_i)\), and equality can fail.

(iii) \(f(X)\setminus f(Y)\subseteq f(X\setminus Y)\), and equality can fail.

(iv) If \(X \subseteq Y\), then \(f(X)\subseteq f(Y)\).

(v) If \(f\) is injective, equality holds in (ii) and (iii).

Beweis. Each clause follows by unwinding definitions; the inclusions in (ii) and (iii) become equalities under injectivity because equal images force equal preimages. \(\blacksquare\)

Satz 0.33 (Preimage and union/intersection/difference/complement; arbitrary families -- full distributivity). Let \(f:A \to B\), \(U,V \subseteq B\), and \((Y_i)_{i\in I}\) a family of subsets of \(B\).

(i) \(f^{-1}(U\cup V)=f^{-1}(U)\cup f^{-1}(V)\); more generally \(f^{-1}(\bigcup_i Y_i)=\bigcup_i f^{-1}(Y_i)\).

(ii) \(f^{-1}(U\cap V)=f^{-1}(U)\cap f^{-1}(V)\); more generally \(f^{-1}(\bigcap_i Y_i)=\bigcap_i f^{-1}(Y_i)\).

(iii) \(f^{-1}(U\setminus V)=f^{-1}(U)\setminus f^{-1}(V)\); in particular \(f^{-1}(B\setminus U)=A\setminus f^{-1}(U)\).

(iv) If \(U\subseteq V\), then \(f^{-1}(U)\subseteq f^{-1}(V)\).

Beweis. All four are pure "unwind the definitions and match propositional connectives" arguments. \(\blacksquare\)

Satz 0.34 (Round trips: image-of-preimage and preimage-of-image). Let \(f:A \to B\).

(i) For \(Y \subseteq B\): \(f(f^{-1}(Y))\subseteq Y\), with equality iff \(Y\subseteq f(A)\) (in particular, equality for every \(Y\) iff \(f\) is surjective).

(ii) For \(X \subseteq A\): \(f^{-1}(f(X))\supseteq X\), with equality for every \(X\) iff \(f\) is injective.

Beweis. Direct from definitions; equality in (i) requires every element of \(Y\) to be hit by \(f\), and equality in (ii) requires no two distinct elements to be identified by \(f\). \(\blacksquare\)

## Chapter 1 -- Laws of a Single Binary Operation

Note. Fix one set \(S\) and one operation \(*:S\times S\to S\). Everything in this chapter is a property \(*\) may or may not have; nothing here presumes \(S\) is a number system. This is the vocabulary in which every later law will be a special case.

### 1.1 Associativity, Commutativity

Definition 1.1 (Associativity).

\[
* \text{ is associative} \iff \forall x,y,z\in S:\ (x*y)*z=x*(y*z).
\]

Definition 1.2 (Commutativity).

\[
* \text{ is commutative} \iff \forall x,y\in S:\ x*y=y*x.
\]

Satz 1.3 (Generalized associativity). If \(*\) is associative, every finite product \(x_1*\cdots*x_n\) (\(n\geq 1\)) is independent of the placement of parentheses, and hence may be written unambiguously without parentheses.

Beweis. Induction on \(n\), using associativity to move between any two outermost splittings. \(\blacksquare\)

Satz 1.4 (Commuting factors under associativity). If \(*\) is associative and commutative, then for \(n\geq 1\) and any permutation \(\sigma\) of \(1,\dots,n\), \(x_{\sigma(1)}*\cdots*x_{\sigma(n)}=x_1*\cdots*x_n\).

Beweis. Every permutation is a product of adjacent transpositions; each adjacent transposition leaves the value unchanged by commutativity inside the unambiguous product from Satz 1.3. \(\blacksquare\)

### 1.2 Identity Elements

Definition 1.5 (Left/right/two-sided identity). \(e\in S\) is a:

- left identity for \(*\) iff for all \(x\in S\): \(e*x=x\);
- right identity for \(*\) iff for all \(x\in S\): \(x*e=x\);
- two-sided identity iff both.

Satz 1.6 (Uniqueness of a two-sided identity). \(*\) has at most one two-sided identity; more generally, if \(e\) is a left identity and \(e'\) is a right identity, then \(e=e'\).

Beweis. \(e=e*e'=e'\). \(\blacksquare\)

Remark 1.7. A left identity need not be unique or equal to a right identity if the latter fails to exist or \(*\) is not coherent in the above sense.

### 1.3 Absorbing (Zero) Elements

Definition 1.8 (Left/right/two-sided absorbing element). \(z\in S\) is a:

- left absorbing element iff for all \(x\in S\): \(z*x=z\);
- right absorbing element iff for all \(x\in S\): \(x*z=z\);
- two-sided absorbing element iff both.

Satz 1.9 (Uniqueness of a two-sided absorbing element). \(*\) has at most one two-sided absorbing element; if \(z\) is left-absorbing and \(z'\) is right-absorbing, then \(z=z'\).

Beweis. \(z=z*z'=z'\). \(\blacksquare\)

Satz 1.10. If \(S\) has more than one element, no element can be simultaneously a two-sided identity and a two-sided absorbing element for the same \(*\).

Beweis. If \(e\) were both, then for any \(x\in S\), \(x=e*x=e\), so \(S\) has one element. \(\blacksquare\)

### 1.4 Idempotence, Involutions

Definition 1.11 (Idempotent element). \(x\in S\) is idempotent for \(*\) iff \(x*x=x\).

Satz 1.12. A two-sided identity, and a two-sided absorbing element, are each idempotent.

Beweis. \(e*e=e\) and \(z*z=z\) by the relevant defining law. \(\blacksquare\)

### 1.5 Inverses

Definition 1.13 (Left/right/two-sided inverse, relative to an identity \(e\)). Suppose \(*\) has two-sided identity \(e\). For \(x\in S\), \(y\in S\) is a:

- left inverse of \(x\) iff \(y*x=e\);
- right inverse of \(x\) iff \(x*y=e\);
- two-sided inverse of \(x\) iff both.

Write \(x^{-1}\) for a two-sided inverse when it is unique.

Satz 1.14 (Left inverse + right inverse implies equal, if associative). Suppose \(*\) is associative with two-sided identity \(e\). If \(y\) is a left inverse of \(x\) and \(y'\) is a right inverse of \(x\), then \(y=y'\).

Beweis. \(y=y*e=y*(x*y')=(y*x)*y'=e*y'=y'\). \(\blacksquare\)

Satz 1.15 (Uniqueness of two-sided inverses, if associative). Under the hypotheses of Satz 1.14, if \(x\) has a two-sided inverse, it is unique.

Beweis. Immediate from Satz 1.14. \(\blacksquare\)

Satz 1.16 (Inverse of a product). If \(*\) is associative with identity \(e\) and \(x,y\in S\) both possess two-sided inverses, then \(x*y\) possesses a two-sided inverse, namely \(y^{-1}*x^{-1}\).

Beweis. Compute both \((x*y)*(y^{-1}*x^{-1})\) and \((y^{-1}*x^{-1})*(x*y)\), using associativity and the inverse laws. \(\blacksquare\)

Satz 1.17 (Involution of inverse). Under the hypotheses of Satz 1.16, if \(x\) has a two-sided inverse \(x^{-1}\), then \(x^{-1}\) has a two-sided inverse, namely \(x\) itself; i.e. \((x^{-1})^{-1}=x\).

Beweis. Immediate from Def. 1.13 read in both directions, plus uniqueness. \(\blacksquare\)

### 1.6 Cancellation Laws

Definition 1.18 (Left/right cancellative operation). \(*\) is:

- left cancellative iff for all \(x,y,z\in S\): \(x*y=x*z\) implies \(y=z\);
- right cancellative iff for all \(x,y,z\in S\): \(y*x=z*x\) implies \(y=z\);
- cancellative iff both.

Satz 1.19. If \(*\) is associative with identity \(e\) and every element of \(S\) has a two-sided inverse, then \(*\) is cancellative.

Beweis. If \(x*y=x*z\), left-multiply by \(x^{-1}\) and simplify. Right cancellation is symmetric. \(\blacksquare\)

Satz 1.20 (Cancellation determines quotient/difference uniquely). If \(*\) is left cancellative, then for fixed \(x,a\in S\), there is at most one \(y\in S\) with \(x*y=a\).

Beweis. If \(x*y=a=x*y'\), left cancellativity gives \(y=y'\). \(\blacksquare\)

### 1.7 Left/Right and Two-Sided Laws in General

Definition 1.21 (Left/right law, schematically). For any predicate \(P(x)\) expressible using \(*\), left/right-paired families include identity, absorbing/zero, inverse, cancellation, and distributivity laws.

Satz 1.22 (Commutativity collapses left/right). If \(*\) is commutative, every left-version property above holds iff the corresponding right-version property holds (for the same witness element).

Beweis. Immediate from \(e*x=x*e\), \(z*x=x*z\), and analogous pointwise commutations. \(\blacksquare\)

Remark 1.23 (Where is "transitivity" for an operation?). Transitivity is a property of a relation, not of an operation. But every associative operation induces a preorder: for a monoid \((S,*,e)\), define \(x \preceq y\) iff there exists \(z\in S\) with \(x*z=y\). Satz 1.24 shows \(\preceq\) is automatically reflexive and transitive.

Satz 1.24 (The divisibility preorder of a monoid). Let \((S,*,e)\) be a monoid. Then \(\preceq\) is a preorder. If in addition \(*\) is commutative, \(\preceq\) is compatible with \(*\): \(x\preceq y\) implies \(x*w\preceq y*w\) for all \(w\).

Beweis. Reflexive: \(x*e=x\). Transitive: if \(x*z=y\) and \(y*z'=w\), then \(x*(z*z')=(x*z)*z'=w\). Compatibility in the commutative case uses \((x*w)*z=x*(w*z)=x*(z*w)=(x*z)*w=y*w\). \(\blacksquare\)

## Chapter 2 -- Two Operations Together: Distributivity and the Ring Skeleton

Note. Arithmetic is never just one operation; \(+\) and \(\times\) interact. Distributivity is the single law tying them together, and it is what makes "\(\times\) is repeated \(+\)" formally sensible.

Definition 2.1 (Left/right/two-sided distributivity of \(\times\) over \(+\)). For operations \(+,\times:S\times S\to S\):

\[
\times \text{ left-distributes over } + \iff
\forall x,y,z\in S:\ x\times(y+z)=(x\times y)+(x\times z).
\]

\[
\times \text{ right-distributes over } + \iff
\forall x,y,z\in S:\ (y+z)\times x=(y\times x)+(z\times x).
\]

\(\times\) distributes over \(+\) iff both.

Satz 2.2. If \(\times\) is commutative, left-distributivity of \(\times\) over \(+\) is equivalent to right-distributivity.

Beweis. Special case of Satz 1.22. \(\blacksquare\)

Satz 2.3 (Distributivity over absorbing/zero). Suppose \(\times\) distributes over \(+\), \(+\) has identity \(0\), and \(+\) is cancellative. Then \(0\times x=0\) and \(x\times 0=0\) for all \(x\).

Beweis. \(0\times x+0\times x=(0+0)\times x=0\times x=0\times x+0\). By cancellation, \(0\times x=0\). The other side is symmetric. \(\blacksquare\)

Satz 2.4 (Distributivity and negation -- the "law of signs," abstractly). Suppose \((S,+,\times)\) satisfies: \(+\) is associative, commutative, has identity \(0\), every element has a \(+\)-inverse, and \(\times\) distributes over \(+\). Then:

(i) \((-x)\times y=-(x\times y)\);

(ii) \((-x)\times(-y)=x\times y\).

Beweis. For (i), \(x\times y+(-x)\times y=(x+(-x))\times y=0\times y=0\), so \((-x)\times y\) is the additive inverse of \(x\times y\). For (ii), apply (i) twice and use involution of additive inverse. \(\blacksquare\)

Satz 2.5 (Absorbing element has no multiplicative inverse, if \(|S|>1\)). In the setting of Satz 2.3, if \(0\) is the \(+\)-identity and \(1\neq 0\) is a \(\times\)-identity, then there is no \(y\) with \(0\times y=1\).

Beweis. By Satz 2.3, \(0\times y=0\) for every \(y\), so \(0\times y=1\) would imply \(0=1\). \(\blacksquare\)

## Chapter 3 -- The Standard Hierarchy of Algebraic Structures

Note. Chapters 1-2 catalogued properties an operation (or pair of operations) may have. This chapter names the packages of properties that recur so often they get their own words.

Definition 3.1 (Magma, semigroup, monoid, group). Let \(*:S\times S\to S\).

- \((S,*)\) is a magma: no further axioms.
- \((S,*)\) is a semigroup iff \(*\) is associative.
- \((S,*)\) is a monoid iff it is a semigroup with a two-sided identity \(e\).
- \((S,*)\) is a group iff it is a monoid in which every element has a two-sided inverse.
- Any of the above is abelian (or commutative) iff \(*\) is commutative.

Satz 3.2 (Groups are cancellative). Every group is cancellative.

Beweis. Immediate from Satz 1.19. \(\blacksquare\)

Definition 3.3 (Semiring, ring, commutative ring, ring with unity, domain, field). Let \(+,\times:S\times S\to S\).

- \((S,+,\times)\) is a semiring iff \((S,+)\) is a commutative monoid, \((S,\times)\) is a semigroup, and \(\times\) distributes over \(+\).
- \((S,+,\times)\) is a ring iff additionally \((S,+)\) is a group.
- A ring is commutative iff \(\times\) is commutative.
- A ring has unity iff \((S,\times)\) is a monoid, i.e. has a \(\times\)-identity \(1\).
- A nontrivial commutative ring with unity is an integral domain iff it has no zero divisors: \(xy=0\) implies \(x=0\) or \(y=0\).
- A nontrivial commutative ring with unity is a field iff every \(x\neq 0\) has a \(\times\)-inverse.

Satz 3.4 (Every field is an integral domain).

Beweis. Let \(xy=0\) and \(x\neq 0\). Since \(S\) is a field, \(x^{-1}\) exists. Then \(x^{-1}(xy)=(x^{-1}x)y=1y=y\), while \(x^{-1}0=0\). Hence \(y=0\). \(\blacksquare\)

Satz 3.5 (Cross-multiplication / determinateness of quotients in a field). In a field, for \(b,d\neq 0\): \(a/b=c/d\) iff \(ad=bc\), where \(a/b:=a\times b^{-1}\).

Beweis. Multiply by \(bd\) in one direction; reverse the computation in the other, using inverses and commutativity. \(\blacksquare\)

## Chapter 4 -- Order

Note. So far nothing has compared elements in size -- only tested equality. This chapter adds \(<\) abstractly and asks what it must satisfy to interact sensibly with \(+\) and \(\times\), producing the notion of ordered field that \(Q\) and \(R\) instantiate.

Definition 4.1 (Strict linear order). A relation \(<\) on \(S\) is a strict linear (total) order iff, for all \(x,y,z\in S\):

- (O1) Irreflexivity: not \((x<x)\);
- (O2) Transitivity: \(x<y\) and \(y<z\) implies \(x<z\);
- (O3) Trichotomy: exactly one of \(x<y\), \(x=y\), \(y<x\) holds.

Definition 4.2 (Derived relations). Define \(x\leq y\) iff \(x<y\) or \(x=y\); define \(x>y\) iff \(y<x\), and \(x\geq y\) iff \(y\leq x\).

Satz 4.3 (Basic properties of \(\leq\)). For all \(x,y,z\in S\):

(i) \(x\leq x\) (reflexivity);

(ii) \(x\leq y\) and \(y\leq x\) imply \(x=y\) (antisymmetry);

(iii) \(x\leq y\) and \(y\leq z\) imply \(x\leq z\) (transitivity);

(iv) \(x\leq y\) or \(y\leq x\) (totality/comparability).

Beweis. This is Satz 0.10 in the direction \(< \rightsquigarrow \leq\), with trichotomy adding totality. \(\blacksquare\)

Definition 4.4 (Compatibility with \(+\): ordered group). Let \((S,+)\) be an abelian group with order \(<\). \(<\) is translation-invariant iff \(x<y\) iff \(x+z<y+z\) for all \(x,y,z\). \((S,+,<)\) is then an ordered abelian group.

Satz 4.5 (Adding inequalities). In an ordered group: \(x<y\) and \(x'<y'\) imply \(x+x'<y+y'\).

Beweis. \(x<y\) gives \(x+x'<y+x'\). \(x'<y'\) gives \(y+x'<y+y'\). Chain by transitivity. \(\blacksquare\)

Satz 4.6 (Sign of an element vs. sign of its negative). In an ordered group with identity \(0\): \(x>0\) iff \(-x<0\).

Beweis. Translate \(x>0\) by adding \(-x\). \(\blacksquare\)

Definition 4.7 (Compatibility with \(\times\): ordered ring / field). Let \((S,+,\times,<)\) be an ordered group under \(+\) with a ring (or field) structure. \(<\) is compatible with \(\times\) iff \(x>0\) and \(y>0\) imply \(xy>0\). \((S,+,\times,<)\) is then an ordered ring (resp. ordered field if \((S,+,\times)\) is a field).

Satz 4.8 (Rule of signs, order form). In an ordered ring:

(i) \(x>0\) and \(y<0\) imply \(xy<0\);

(ii) \(x<0\) and \(y<0\) imply \(xy>0\);

(iii) \(x\neq 0\) implies \(x^2>0\); in particular \(1>0\) in any nontrivial ordered ring with unity.

Beweis. Use Satz 4.6 to replace negative factors by positives and Satz 2.4 for algebraic signs. For (iii), apply trichotomy to \(x\). \(\blacksquare\)

Satz 4.9 (Multiplying an inequality by a positive/negative element). In an ordered ring, for \(x<y\):

(i) \(z>0\) implies \(xz<yz\);

(ii) \(z<0\) implies \(xz>yz\).

Beweis. \(x<y\) iff \(y-x>0\). If \(z>0\), then \((y-x)z>0\), so \(yz-xz>0\), hence \(xz<yz\). If \(z<0\), apply (i) to \(-z>0\) and reverse signs. \(\blacksquare\)

Satz 4.10 (No order makes \(C\) an ordered field). There is no relation \(<\) on \(C\) satisfying Def. 4.1, 4.4, 4.7 simultaneously with the usual field structure.

Beweis. In an ordered field, every nonzero square is positive. Thus \(1=i^2? \) More precisely, \(1^2>0\) gives \(1>0\), and \(i^2=-1\) gives \(-1>0\). But \(1>0\) implies \(-1<0\), contradiction. \(\blacksquare\)

Definition 4.11 (Trichotomy law for products -- abstract form of Fine's Law IX'). A product comparison law is the corresponding multiplication-by-positive/negative rule for the compared pair.

Satz 4.12. This is exactly Satz 4.9 restated with the roles of the multiplier and compared pair swapped; no new proof is required.

## Chapter 5 -- Absolute Value

Note. Absolute value packages "distance from 0," and is definable purely from an order -- no extra structure needed beyond Chapter 4.

Definition 5.1 (Absolute value). In an ordered group \((S,+,<)\) with identity \(0\):

\[
|x| :=
\begin{cases}
x, & x\geq 0,\\
-x, & x<0.
\end{cases}
\]

Satz 5.2 (Basic properties). For all \(x,y\in S\) (ordered ring):

(i) \(|x|\geq 0\), with equality iff \(x=0\);

(ii) \(|-x|=|x|\);

(iii) \(-|x|\leq x\leq |x|\);

(iv) \(|xy|=|x||y|\);

(v) \(|x+y|\leq |x|+|y|\) (triangle inequality);

(vi) \(||x|-|y||\leq |x-y|\).

Beweis. Case-split by signs using trichotomy and Satz 4.8; for (v), add the bounds in (iii), and for (vi), apply (v) to \(x=(x-y)+y\) and symmetrically. \(\blacksquare\)

## Chapter 6 -- Subtraction and Division as Inverse Operations, Abstractly

Note. Fine's Chapters 1-3 devote real effort to defining subtraction and division as "the determinate solution of an equation," rather than as primitive operations. This chapter restates that construction once, abstractly.

Definition 6.1 (Inverse operation, generally). Let \((S,*)\) be a cancellative monoid-or-partial-structure with identity \(e\). The inverse operation \(*^{-1}\) is defined on the domain \(D\subseteq S\times S\) of pairs \((a,b)\) for which there exists a solution \(x\) to \(x*b=a\); \(a*^{-1}b\) is that unique \(x\), uniqueness guaranteed by right-cancellativity.

Satz 6.2 (Subtraction is \(+^{-1}\)). For \((S,+)\) a cancellative commutative monoid, define \(a-b:=a+^{-1}b\), i.e. the unique \(x\) (when it exists) with \(x+b=a\). Then subtraction satisfies the usual cancellation identities on its domain.

Beweis. The first identity is Def. 6.1. Associativity and commutativity reduce nested differences to the corresponding unique solutions. \(\blacksquare\)

Satz 6.3 (When does \(a-b\) always exist? -- the negative, abstractly). \(*^{-1}\) is defined on all of \(S\times S\) iff every element of \(S\) has a \(*\)-inverse, i.e. iff \((S,*)\) is a group.

Beweis. In a group, \(a*b^{-1}\) solves \(x*b=a\). Conversely, if every such solution exists, taking \(a=e\) supplies inverses. \(\blacksquare\)

Satz 6.4 (Division is \(\times^{-1}\)). For \((S\setminus\{0\},\times)\) a commutative group (i.e. \(S\) a field), define \(a/b:=a\times b^{-1}\) for \(b\neq 0\). The usual laws of fractions follow by group calculation and distributivity.

Beweis. Direct computation in the field. \(\blacksquare\)

Satz 6.5 (Division by the absorbing element is impossible). In a field \(S\), \(0\) has no multiplicative inverse if \(|S|>1\).

Beweis. Satz 2.5 specialized to a field. \(\blacksquare\)

## Chapter 7 -- Exponentiation

Note. Exponentiation is iterated multiplication for natural exponents, and the definition must be extended -- by the same permanence-of-form logic Fine uses throughout -- to make sense for zero, negative, and eventually rational/real exponents, while preserving the laws that hold for natural-number exponents.

Definition 7.1 (Natural-number powers, recursively). Let \((S,\times)\) be a monoid with identity \(1\). For \(x\in S\), define \(x^0:=1\) and \(x^{n+1}:=x^n\times x\).

Satz 7.2 (Laws of exponents, natural exponents). For \(x,y\in S\), \(m,n\in \mathbb N\cup\{0\}\):

(i) \(x^m x^n=x^{m+n}\);

(ii) \((x^m)^n=x^{mn}\);

(iii) if \(\times\) is commutative, \((xy)^n=x^n y^n\).

Beweis. Induction on exponents, using associativity and, for (iii), commutativity. \(\blacksquare\)

Definition 7.3 (Negative integer exponents, via permanence). If \(x\in S\) has a \(\times\)-inverse \(x^{-1}\), extend Def. 7.1 by declaring \(x^{-n}:=(x^{-1})^n\) for \(n\in \mathbb N\).

Satz 7.4. \((x^n)^{-1}=(x^{-1})^n\) whenever \(x^{-1}\) exists.

Beweis. Induction on \(n\), using associativity and inverse laws; uniqueness of inverses identifies the inverse. \(\blacksquare\)

Satz 7.5 (Laws of exponents extend to all integers). For \(x\) invertible, Satz 7.2(i),(ii) hold for all \(m,n\in \mathbb Z\).

Beweis. Case-split on signs and reduce to Satz 7.2 and Satz 7.4. \(\blacksquare\)

Remark 7.6 (Rational and real exponents). Extending \(x^q\) to \(q\in \mathbb Q\) and \(q\in \mathbb R\) requires analytic input beyond pure algebra -- completeness of \(S\) -- and is deliberately not re-derived here.

## Chapter 8 -- Floor and Ceiling

Note. Floor and ceiling are the bridge from a dense/continuous ordered field back to the discrete integers sitting inside it.

Definition 8.1 (Archimedean ordered field). An ordered field \(S\supseteq \mathbb Z\) is Archimedean iff for all \(x\in S\), there exists \(n\in \mathbb Z\) with \(n>x\).

Satz 8.2 (Existence and uniqueness of the floor). If \(S\) is Archimedean, then for every \(x\in S\) there is a unique \(n\in \mathbb Z\) with \(n\leq x<n+1\).

Beweis. The set \(T:=\{m\in\mathbb Z:m\leq x\}\) is nonempty and bounded above by Archimedeanness; a nonempty bounded-above set of integers has a greatest element. Uniqueness follows from antisymmetry in \(\mathbb Z\). \(\blacksquare\)

Definition 8.3 (Floor and ceiling). Define \(\lfloor x\rfloor\) as the unique \(n\) with \(n\leq x<n+1\), and \(\lceil x\rceil\) as the unique \(n\) with \(n-1<x\leq n\).

Satz 8.4 (Ceiling from floor). \(\lceil x\rceil=-\lfloor -x\rfloor\).

Beweis. Negate the defining inequalities for \(\lfloor -x\rfloor\). \(\blacksquare\)

Satz 8.5 (Idempotence and integer fixed points). For \(n\in \mathbb Z\), \(\lfloor n\rfloor=n=\lceil n\rceil\). Consequently \(\lfloor\lfloor x\rfloor\rfloor=\lfloor x\rfloor\) and \(\lceil\lceil x\rceil\rceil=\lceil x\rceil\).

Beweis. \(n\leq n<n+1\), and similarly for ceiling; idempotence follows because floors and ceilings are integers. \(\blacksquare\)

Satz 8.6 (Monotonicity). \(x\leq y\) implies \(\lfloor x\rfloor\leq \lfloor y\rfloor\) and \(\lceil x\rceil\leq \lceil y\rceil\).

Beweis. If \(\lfloor x\rfloor>\lfloor y\rfloor\), then \(y<\lfloor y\rfloor+1\leq \lfloor x\rfloor\leq x\), contradicting \(x\leq y\). Ceiling follows by duality. \(\blacksquare\)

Satz 8.7 (Floor/ceiling of a sum with an integer). For \(n\in \mathbb Z\), \(\lfloor x+n\rfloor=\lfloor x\rfloor+n\) and \(\lceil x+n\rceil=\lceil x\rceil+n\).

Beweis. Add \(n\) throughout the defining inequalities. \(\blacksquare\)

Satz 8.8 (Sub/super-additivity of floor). For \(x,y\in S\):

\[
\lfloor x\rfloor+\lfloor y\rfloor
\leq
\lfloor x+y\rfloor
\leq
\lfloor x\rfloor+\lfloor y\rfloor+1.
\]

Beweis. Let \(m=\lfloor x\rfloor\), \(n=\lfloor y\rfloor\). Add \(m\leq x<m+1\) and \(n\leq y<n+1\), then split according to whether \(x+y<m+n+1\) or \(m+n+1\leq x+y\). \(\blacksquare\)

Satz 8.9 (Floor as nearest-integer-below, characterizing inequality). \(n=\lfloor x\rfloor\) is equivalently characterized by \(x-1<n\leq x\).

Beweis. From \(n\leq x<n+1\), subtract \(1\) from the right inequality to get \(x-1<n\); conversely add \(1\). \(\blacksquare\)

Definition 8.10 (Fractional part). \(\{x\}:=x-\lfloor x\rfloor\).

Satz 8.11. \(0\leq \{x\}<1\) for every \(x\in S\).

Beweis. Subtract \(\lfloor x\rfloor\) throughout \(\lfloor x\rfloor\leq x<\lfloor x\rfloor+1\). \(\blacksquare\)

## Chapter 9 -- Reference Table: The Complete Law Catalogue

Note. A single compressed table, gathering every law named above, for quick lookup.

| # | Law | Formal statement | Where proved/defined |
|---|---|---|---|
| L0 | Reflexivity (relation) | \(xRx\) | Def. 0.7 |
| L0' | Symmetry (relation) | \(xRy\Rightarrow yRx\) | Def. 0.7 |
| L0'' | Transitivity (relation) | \(xRy\land yRz\Rightarrow xRz\) | Def. 0.7 |
| L1 | Associativity | \((x*y)*z=x*(y*z)\) | Def. 1.1 |
| L2 | Commutativity | \(x*y=y*x\) | Def. 1.2 |
| L3 | Left identity | \(e*x=x\) | Def. 1.5 |
| L4 | Right identity | \(x*e=x\) | Def. 1.5 |
| L5 | Left absorbing/zero | \(z*x=z\) | Def. 1.8 |
| L6 | Right absorbing/zero | \(x*z=z\) | Def. 1.8 |
| L7 | Idempotence | \(x*x=x\) | Def. 1.11 |
| L8 | Left inverse | \(y*x=e\) | Def. 1.13 |
| L9 | Right inverse | \(x*y=e\) | Def. 1.13 |
| L10 | Left cancellation | \(x*y=x*z\Rightarrow y=z\) | Def. 1.18 |
| L11 | Right cancellation | \(y*x=z*x\Rightarrow y=z\) | Def. 1.18 |
| L11' | Induced preorder | \(x\preceq y\iff \exists z(x*z=y)\) is a preorder | Satz 1.24 |
| L12 | Left distributivity | \(x(y+z)=xy+xz\) | Def. 2.1 |
| L13 | Right distributivity | \((y+z)x=yx+zx\) | Def. 2.1 |
| L14 | No zero divisors | \(xy=0\Rightarrow x=0\lor y=0\) | Def. 3.3, Satz 3.4 |
| L15 | Order irreflexivity | not \((x<x)\) | Def. 4.1 |
| L16 | Order transitivity | \(x<y\land y<z\Rightarrow x<z\) | Def. 4.1 |
| L17 | Trichotomy | exactly one of \(<,=,>\) | Def. 4.1 |
| L18 | Translation invariance | \(x<y\iff x+z<y+z\) | Def. 4.4 |
| L19 | Multiplicative compatibility | \(x,y>0\Rightarrow xy>0\) | Def. 4.7 |
| L20 | Rule of signs | \((-x)(-y)=xy\), \((-x)y=-(xy)\) | Satz 2.4 |
| L21 | Triangle inequality | \(|x+y|\leq |x|+|y|\) | Satz 5.2(v) |
| L22 | Exponent addition | \(x^m x^n=x^{m+n}\) | Satz 7.2(i), 7.5 |
| L23 | Exponent multiplication | \((x^m)^n=x^{mn}\) | Satz 7.2(ii), 7.5 |
| L24 | Power of product | \((xy)^n=x^n y^n\) (commutative case) | Satz 7.2(iii) |
| L25 | Floor characterization | \(n\leq x<n+1\) | Def. 8.3 |
| L26 | Ceiling characterization | \(n-1<x\leq n\) | Def. 8.3 |
| L27 | Floor-ceiling duality | \(\lceil x\rceil=-\lfloor -x\rfloor\) | Satz 8.4 |
| L28 | Floor sub-additivity | \(\lfloor x\rfloor+\lfloor y\rfloor\leq\lfloor x+y\rfloor\leq\lfloor x\rfloor+\lfloor y\rfloor+1\) | Satz 8.8 |
| L29 | Image of union | \(f(X\cup Y)=f(X)\cup f(Y)\) | Satz 0.32(i) |
| L30 | Image of intersection (sub.) | \(f(X\cap Y)\subseteq f(X)\cap f(Y)\) | Satz 0.32(ii) |
| L31 | Preimage of union | \(f^{-1}(U\cup V)=f^{-1}(U)\cup f^{-1}(V)\) | Satz 0.33(i) |
| L32 | Preimage of intersection | \(f^{-1}(U\cap V)=f^{-1}(U)\cap f^{-1}(V)\) | Satz 0.33(ii) |
| L33 | Preimage of complement | \(f^{-1}(B\setminus U)=A\setminus f^{-1}(U)\) | Satz 0.33(iii) |
| L34 | Composition associativity | \((h\circ g)\circ f=h\circ(g\circ f)\) | Satz 0.25 |

## Chapter 10 -- Instantiation: Where N, Z, Q, R Sit in the Hierarchy

Note. Closing the loop back to Fine (and to Landau's actual book): each concrete number system is now nameable in one line, as an instance of Chapter 3's definitions.

Satz 10.1. \((N,+)\) is a commutative, cancellative semigroup without identity in Landau's original construction (Peano-successor built), or a commutative cancellative monoid if \(0\) is included; it is not a group.

Satz 10.2. \((Z,+,\times)\) is a commutative ring with unity \(1\); it is an integral domain; it is not a field.

Satz 10.3. \((Q,+,\times,<)\) is an ordered field; it is Archimedean but not complete, motivating the construction of \(R\).

Satz 10.4. \((R,+,\times,<)\) is a complete Archimedean ordered field; by a classical uniqueness theorem, it is the unique complete ordered field up to order- and operation-preserving isomorphism.

Satz 10.5. \((C,+,\times)\) is a field but admits no order making it an ordered field; floor and ceiling are accordingly undefined on \(C\).

\(\blacksquare\) (End of omnibus.)
