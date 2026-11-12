import 'package:flutter/material.dart';
import '../../core/api.dart';

const accent = Color(0xff9184d9),
    surface = Color(0xff232532),
    muted = Color(0xff9397ab),
    green = Color(0xff8fceac),
    border = Color(0xff3f424d);
const labels = [
  "Vue d'ensemble",
  "Carte temps réel",
  "Motards",
  "Clients",
  "Gérants",
  "Commissions",
  "Notifications",
  "Support",
  "Réglages",
];
const icons = [
  Icons.dashboard_rounded,
  Icons.map_outlined,
  Icons.two_wheeler,
  Icons.people_outline,
  Icons.manage_accounts_outlined,
  Icons.paid_outlined,
  Icons.notifications_none,
  Icons.support_agent,
  Icons.settings_outlined,
];

class DirectionDashboard extends StatefulWidget {
  const DirectionDashboard({super.key});
  @override
  State<DirectionDashboard> createState() => _DashboardState();
}

class _DashboardState extends State<DirectionDashboard> {
  int page = 0;
  bool demo = true;
  String query = '', error = '', name = 'Joseph Kabengele';
  Map<String, dynamic>? live;
  PersonnelApi? api;
  final scaffold = GlobalKey<ScaffoldState>();
  List<Map<String, dynamic>> get riders => demo
      ? [
          {
            'name': 'Trésor Mbuyi',
            'commune': 'Gombe',
            'rides': 38,
            'revenue': 312000,
            'rating': '4,9',
            'pillar': 'Abonnement',
          },
          {
            'name': 'Divine Nsimba',
            'commune': 'Limete',
            'rides': 34,
            'revenue': 286000,
            'rating': '4,8',
            'pillar': 'Gérance · Kin-Express',
          },
          {
            'name': 'Gédéon Kabasele',
            'commune': 'Masina',
            'rides': 31,
            'revenue': 254000,
            'rating': '4,7',
            'pillar': 'Allocation moto',
          },
          {
            'name': 'Patrick Ilunga',
            'commune': 'Ngaliema',
            'rides': 29,
            'revenue': 241000,
            'rating': '4,9',
            'pillar': 'Abonnement',
          },
          {
            'name': 'Merveille Kongo',
            'commune': 'Lemba',
            'rides': 27,
            'revenue': 223000,
            'rating': '4,6',
            'pillar': 'Abonnement',
          },
        ]
      : List<Map<String, dynamic>>.from(live?['top_motards'] ?? []);
  Widget txt(String s, {double size = 13, Color? color, FontWeight? weight}) =>
      Text(
        s,
        style: TextStyle(fontSize: size, color: color, fontWeight: weight),
      );
  Widget box(Widget child, {EdgeInsets padding = const EdgeInsets.all(18)}) =>
      Container(
        padding: padding,
        decoration: BoxDecoration(
          color: surface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: border),
        ),
        child: child,
      );
  void select(int i) {
    setState(() => page = i);
    if (scaffold.currentState?.isDrawerOpen ?? false) Navigator.pop(context);
  }

  Widget side() => Container(
    width: 252,
    color: const Color(0xff171927),
    child: Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 18, 20, 16),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(9),
                decoration: BoxDecoration(
                  color: accent,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(Icons.two_wheeler, color: Colors.white),
              ),
              const SizedBox(width: 11),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  txt('GO-MBOKA', size: 15, weight: FontWeight.bold),
                  txt('DIRECTION GÉNÉRALE', size: 10, color: muted),
                ],
              ),
            ],
          ),
        ),
        Expanded(
          child: ListView(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            children: [
              for (int i = 0; i < labels.length; i++) ...[
                if ([0, 2, 4, 6].contains(i))
                  Padding(
                    padding: const EdgeInsets.fromLTRB(11, 14, 0, 6),
                    child: txt(
                      {
                        0: 'PILOTAGE',
                        2: 'RÉSEAU',
                        4: 'BUSINESS',
                        6: 'SYSTÈME',
                      }[i]!,
                      size: 10,
                      color: muted,
                    ),
                  ),
                Padding(
                  padding: const EdgeInsets.only(bottom: 2),
                  child: Material(
                    color: page == i
                        ? const Color(0xff2b2741)
                        : Colors.transparent,
                    borderRadius: BorderRadius.circular(9),
                    child: ListTile(
                      dense: true,
                      minTileHeight: 38,
                      leading: Icon(
                        icons[i],
                        size: 18,
                        color: page == i ? const Color(0xffd2cefd) : muted,
                      ),
                      title: txt(
                        labels[i],
                        color: page == i ? const Color(0xffe7e5fe) : muted,
                      ),
                      onTap: () => select(i),
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(14),
          child: box(
            Row(
              children: [
                CircleAvatar(
                  radius: 17,
                  backgroundColor: accent,
                  child: txt(demo ? 'JK' : initials(name), size: 11),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      txt(name, size: 12),
                      txt(
                        'Directeur Général · accès total',
                        size: 10,
                        color: muted,
                      ),
                    ],
                  ),
                ),
                InkWell(
                  onTap: () => select(8),
                  child: const Icon(Icons.settings_outlined, size: 17),
                ),
              ],
            ),
            padding: const EdgeInsets.all(11),
          ),
        ),
      ],
    ),
  );
  String initials(String n) =>
      n.split(' ').where((s) => s.isNotEmpty).take(2).map((s) => s[0]).join();
  Future<void> connect() async {
    final url = TextEditingController(
      text: const String.fromEnvironment(
        'API_BASE_URL',
        defaultValue: 'http://127.0.0.1:8000',
      ),
    );
    final user = TextEditingController(), pass = TextEditingController();
    final result = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Connexion du personnel'),
        content: SizedBox(
          width: 380,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: url,
                decoration: const InputDecoration(
                  labelText: 'Adresse du serveur',
                ),
              ),
              TextField(
                controller: user,
                decoration: const InputDecoration(labelText: 'Identifiant'),
              ),
              TextField(
                controller: pass,
                obscureText: true,
                decoration: const InputDecoration(labelText: 'Mot de passe'),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(c, false),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(c, true),
            child: const Text('Se connecter'),
          ),
        ],
      ),
    );
    if (result != true) return;
    try {
      final candidate = PersonnelApi(url.text);
      final me = await candidate.login(user.text, pass.text);
      final data = await candidate.request('/api/dashboard/operator/');
      if (!mounted) return;
      setState(() {
        api = candidate;
        live = data;
        demo = false;
        name = '${me['first_name'] ?? ''} ${me['last_name'] ?? ''}'.trim();
        if (name.isEmpty) name = user.text;
        error = '';
      });
    } catch (e) {
      if (mounted) setState(() => error = 'Connexion impossible : $e');
    }
    pass.clear();
  }

  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, c) {
      final desktop = c.maxWidth >= 1000;
      return Scaffold(
        key: scaffold,
        drawer: desktop ? null : Drawer(child: side()),
        body: SafeArea(
          child: Row(
            children: [
              if (desktop) side(),
              Expanded(
                child: Column(
                  children: [
                    Container(
                      height: 66,
                      padding: EdgeInsets.symmetric(
                        horizontal: desktop ? 26 : 12,
                      ),
                      decoration: const BoxDecoration(
                        border: Border(bottom: BorderSide(color: border)),
                      ),
                      child: Row(
                        children: [
                          if (!desktop)
                            IconButton(
                              onPressed: () =>
                                  scaffold.currentState?.openDrawer(),
                              icon: const Icon(Icons.menu),
                            ),
                          Expanded(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                txt(
                                  labels[page],
                                  size: 16,
                                  weight: FontWeight.w600,
                                ),
                                txt(
                                  demo
                                      ? 'MODE MAQUETTE · données fictives du ZIP'
                                      : 'Kinshasa · Direction Générale',
                                  size: 11,
                                  color: muted,
                                ),
                              ],
                            ),
                          ),
                          if (desktop)
                            SizedBox(
                              width: 260,
                              child: TextField(
                                onChanged: (v) => setState(() => query = v),
                                decoration: const InputDecoration(
                                  isDense: true,
                                  prefixIcon: Icon(Icons.search, size: 18),
                                  hintText:
                                      'Rechercher motard, course, client…',
                                  hintStyle: TextStyle(fontSize: 12),
                                  border: OutlineInputBorder(),
                                ),
                              ),
                            ),
                          IconButton(
                            tooltip: 'Notifications',
                            onPressed: () => select(6),
                            icon: const Icon(
                              Icons.notifications_none,
                              size: 20,
                            ),
                          ),
                          IconButton(
                            tooltip: 'Connexion au serveur',
                            onPressed: connect,
                            icon: const Icon(
                              Icons.account_circle,
                              color: accent,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Expanded(
                      child: SingleChildScrollView(
                        padding: EdgeInsets.all(desktop ? 26 : 16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            if (error.isNotEmpty)
                              Text(
                                error,
                                style: const TextStyle(color: Colors.redAccent),
                              ),
                            if (page == 0)
                              overview(desktop)
                            else if (page == 1)
                              mapPanel()
                            else if (page == 2)
                              network()
                            else if (page == 8)
                              box(
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    txt('Mon profil', size: 18),
                                    Text(name),
                                    const SizedBox(height: 16),
                                    FilledButton(
                                      onPressed: connect,
                                      child: const Text('Connexion au serveur'),
                                    ),
                                    if (!demo)
                                      TextButton(
                                        onPressed: () => setState(() {
                                          api?.token = null;
                                          live = null;
                                          demo = true;
                                          name = 'Joseph Kabengele';
                                        }),
                                        child: const Text('Déconnexion'),
                                      ),
                                  ],
                                ),
                              )
                            else
                              box(
                                Padding(
                                  padding: const EdgeInsets.all(24),
                                  child: txt(
                                    '${labels[page]} · écran en cours de réalisation',
                                    color: muted,
                                  ),
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      );
    },
  );
  Widget overview(bool desktop) {
    final k = live?['kpis'] ?? {};
    final values = demo
        ? ['1 284', '342 / 468', '8,4M FC', '4,7 / 5']
        : [
            '${k['total_rides'] ?? 0}',
            '${k['active_motards'] ?? 0} / ${k['total_motards'] ?? 0}',
            '${k['revenue_fc'] ?? 0} FC',
            '${k['avg_rating'] ?? 0} / 5',
          ];
    final titles = [
      "Courses aujourd’hui",
      'Motards actifs',
      'Revenus du jour · ≈ ${demo ? "\$2 980" : k['revenue_usd'] ?? 0}',
      'Note moyenne réseau',
    ];
    final cards = [
      for (int i = 0; i < 4; i++)
        box(
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Icon(
                    [Icons.route, Icons.two_wheeler, Icons.paid, Icons.star][i],
                    color: i == 1 ? green : accent,
                    size: 23,
                  ),
                  txt(
                    demo
                        ? ['↗ +12%', '73% en ligne', '↗ +8%', '2 314 avis'][i]
                        : '',
                    size: 11,
                    color: green,
                  ),
                ],
              ),
              const SizedBox(height: 12),
              txt(values[i], size: 27, weight: FontWeight.bold),
              txt(titles[i], size: 12, color: muted),
            ],
          ),
        ),
    ];
    return Column(
      children: [
        LayoutBuilder(
          builder: (c, b) => Wrap(
            spacing: 16,
            runSpacing: 16,
            children: [
              for (final card in cards)
                SizedBox(
                  width: (b.maxWidth - (desktop ? 48 : 16)) / (desktop ? 4 : 2),
                  height: desktop ? 142 : 158,
                  child: card,
                ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        if (desktop)
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(flex: 155, child: mapPanel()),
              const SizedBox(width: 16),
              Expanded(
                flex: 100,
                child: Column(
                  children: [activity(), const SizedBox(height: 16), top()],
                ),
              ),
            ],
          )
        else ...[
          mapPanel(),
          const SizedBox(height: 16),
          activity(),
          const SizedBox(height: 16),
          top(),
        ],
        const SizedBox(height: 18),
        network(),
      ],
    );
  }

  Widget mapPanel() => box(
    Column(
      children: [
        Row(
          children: [
            const Icon(Icons.location_on, color: accent, size: 18),
            const SizedBox(width: 8),
            Expanded(
              child: txt(
                'Positions en temps réel — Kinshasa',
                weight: FontWeight.w600,
              ),
            ),
          ],
        ),
        const SizedBox(height: 14),
        if (demo)
          LayoutBuilder(
            builder: (context, c) => SizedBox(
              height: c.maxWidth < 500 ? 280 : 464,
              width: double.infinity,
              child: const CustomPaint(painter: KinshasaPainter()),
            ),
          )
        else
          const SizedBox(
            height: 452,
            child: Center(
              child: Text('Positions GPS : intégration à poursuivre'),
            ),
          ),
        Align(
          alignment: Alignment.centerLeft,
          child: txt(
            demo
                ? 'Toutes communes     ·     Demandes en attente · 7'
                : 'Aucune position simulée',
            size: 11,
            color: muted,
          ),
        ),
      ],
    ),
    padding: const EdgeInsets.all(16),
  );
  Widget activity() => box(
    Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        txt('Activité de la journée', weight: FontWeight.w600),
        const SizedBox(height: 6),
        txt('■ Déplacements    ━ Revenus', size: 11, color: muted),
        const SizedBox(height: 14),
        SizedBox(
          height: 120,
          child: Stack(
            fit: StackFit.expand,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  for (int i = 0; i < 15; i++)
                    Expanded(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 2),
                        child: Container(
                          height: demo
                              ? [
                                      14,
                                      38,
                                      71,
                                      60,
                                      48,
                                      53,
                                      76,
                                      66,
                                      45,
                                      57,
                                      81,
                                      100,
                                      90,
                                      67,
                                      41,
                                    ][i] *
                                    1.2
                              : ((live?['activity']?['${i + 6}']?['count'] ?? 0)
                                        as num)
                                    .toDouble()
                                    .clamp(0, 120),
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                              begin: Alignment.topCenter,
                              end: Alignment.bottomCenter,
                              colors: [Color(0xffb5abfc), Color(0xff5d5294)],
                            ),
                            borderRadius: BorderRadius.circular(3),
                          ),
                        ),
                      ),
                    ),
                ],
              ),
              if (demo) const CustomPaint(painter: RevenuePainter()),
            ],
          ),
        ),
        const SizedBox(height: 6),
        txt(
          '06h           09h           12h           15h           18h',
          size: 10,
          color: muted,
        ),
      ],
    ),
  );
  Widget top() => box(
    Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        txt('Top motards du jour', weight: FontWeight.w600),
        const SizedBox(height: 12),
        for (final (i, m) in riders.indexed)
          Padding(
            padding: const EdgeInsets.only(bottom: 11),
            child: Row(
              children: [
                txt('${i + 1}', color: accent),
                const SizedBox(width: 11),
                CircleAvatar(
                  radius: 15,
                  backgroundColor: border,
                  child: txt(initials(m['name']), size: 10),
                ),
                const SizedBox(width: 11),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      txt(m['name'], size: 12),
                      txt(
                        '${m['commune'] ?? '—'} · ${m['rides']} courses',
                        size: 10,
                        color: muted,
                      ),
                    ],
                  ),
                ),
                Column(
                  children: [
                    txt('${(m['revenue'] as num) / 1000}k FC', size: 12),
                    txt(
                      '★ ${m['rating']}',
                      size: 10,
                      color: const Color(0xffd9a866),
                    ),
                  ],
                ),
              ],
            ),
          ),
      ],
    ),
  );
  Widget network() => box(
    Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Expanded(child: txt('Motards du réseau', weight: FontWeight.w600)),
            TextButton(
              onPressed: () => select(2),
              child: const Text('Tout voir'),
            ),
          ],
        ),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: DataTable(
            headingTextStyle: const TextStyle(color: muted, fontSize: 11),
            dataTextStyle: const TextStyle(fontSize: 12),
            columnSpacing: 28,
            columns: [
              for (final s in [
                'Motard',
                'Commune',
                'Statut',
                'Courses',
                'Revenu (jour)',
                'Note',
                'Pilier',
              ])
                DataColumn(label: Text(s)),
            ],
            rows: [
              for (final m in riders.where(
                (m) => m['name'].toString().toLowerCase().contains(
                  query.toLowerCase(),
                ),
              ))
                DataRow(
                  cells: [
                    DataCell(Text(m['name'])),
                    DataCell(Text(m['commune'] ?? '—')),
                    DataCell(
                      txt(demo ? 'En course' : '—', color: accent, size: 11),
                    ),
                    DataCell(Text('${m['rides']}')),
                    DataCell(Text('${m['revenue']} FC')),
                    DataCell(Text('★ ${m['rating']}')),
                    DataCell(Text(m['pillar'] ?? '—')),
                  ],
                ),
            ],
          ),
        ),
      ],
    ),
  );
}

class KinshasaPainter extends CustomPainter {
  const KinshasaPainter();
  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.scale(size.width / 400, size.height / 260);
    canvas.drawRect(
      const Rect.fromLTWH(0, 0, 400, 260),
      Paint()..color = const Color(0xff191d2e),
    );
    final p = Paint()
      ..color = border
      ..strokeWidth = 7
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;
    for (final points in [
      [
        const Offset(38, 18),
        const Offset(120, 118),
        const Offset(206, 108),
        const Offset(262, 198),
      ],
      [const Offset(0, 86), const Offset(400, 116)],
      [const Offset(150, 0), const Offset(172, 206)],
      [const Offset(300, 8), const Offset(280, 138), const Offset(360, 236)],
    ]) {
      final path = Path()..moveTo(points[0].dx, points[0].dy);
      for (final q in points.skip(1)) {
        path.lineTo(q.dx, q.dy);
      }
      canvas.drawPath(path, p);
    }
    p.strokeWidth = 2.5;
    p.color = const Color(0xff595d6c);
    canvas.drawPath(
      Path()
        ..moveTo(60, 40)
        ..lineTo(200, 70)
        ..lineTo(330, 40),
      p,
    );
    canvas.drawPath(
      Path()
        ..moveTo(90, 150)
        ..lineTo(240, 140)
        ..lineTo(340, 180),
      p,
    );
    final river = Path()
      ..moveTo(0, 208)
      ..cubicTo(80, 188, 130, 236, 210, 220)
      ..cubicTo(300, 204, 342, 250, 400, 228)
      ..lineTo(400, 260)
      ..lineTo(0, 260)
      ..close();
    canvas.drawPath(river, Paint()..color = const Color(0xff292f48));
    for (final (s, x, y) in [
      ('GOMBE', 36.0, 34.0),
      ('LINGWALA', 150.0, 62.0),
      ('MASINA', 300.0, 52.0),
      ('NGALIEMA', 24.0, 120.0),
      ('LIMETE', 212.0, 102.0),
      ('LEMBA', 118.0, 182.0),
      ('NDJILI', 300.0, 150.0),
    ]) {
      final t = TextPainter(
        text: TextSpan(
          text: s,
          style: const TextStyle(
            color: muted,
            fontSize: 9,
            fontFamily: 'Inter',
            letterSpacing: 1,
          ),
        ),
        textDirection: TextDirection.ltr,
      )..layout();
      t.paint(canvas, Offset(x, y));
    }
    for (final (x, y, c) in [
      (120.0, 67.0, accent),
      (64.0, 122.0, accent),
      (248.0, 130.0, accent),
      (320.0, 99.0, accent),
      (160.0, 114.0, accent),
      (168.0, 52.0, green),
      (280.0, 156.0, green),
      (188.0, 182.0, green),
      (352.0, 166.0, green),
    ]) {
      canvas.drawCircle(Offset(x, y), 6, Paint()..color = Colors.white);
      canvas.drawCircle(Offset(x, y), 4.5, Paint()..color = c);
    }
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class RevenuePainter extends CustomPainter {
  const RevenuePainter();
  @override
  void paint(Canvas c, Size s) {
    const values = [
      101,
      76,
      48,
      57,
      66,
      61,
      37,
      48,
      72,
      60,
      33,
      13,
      21,
      45,
      74,
    ];
    final path = Path();
    for (int i = 0; i < values.length; i++) {
      final x = (i + .5) * s.width / 15;
      final y = values[i] * s.height / 120;
      i == 0 ? path.moveTo(x, y) : path.lineTo(x, y);
    }
    c.drawPath(
      path,
      Paint()
        ..color = green
        ..strokeWidth = 2
        ..style = PaintingStyle.stroke,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
