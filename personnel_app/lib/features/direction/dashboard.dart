import 'dart:async';
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
  const DirectionDashboard({super.key, this.initialApi});
  final PersonnelApi? initialApi;
  @override
  State<DirectionDashboard> createState() => _State();
}

class _State extends State<DirectionDashboard> {
  PersonnelApi? api;
  Map<String, dynamic>? data;
  int page = 0;
  bool busy = false;
  String error = '', query = '', statusFilter = 'Tous';
  Timer? timer;
  final scaffold = GlobalKey<ScaffoldState>();
  @override
  void initState() {
    super.initState();
    api = widget.initialApi;
    if (api != null) unawaited(load());
    timer = Timer.periodic(const Duration(seconds: 30), (_) {
      if (api != null && !busy) unawaited(load());
    });
  }

  @override
  void dispose() {
    timer?.cancel();
    super.dispose();
  }

  Future<void> load() async {
    if (api == null) return;
    setState(() => busy = true);
    try {
      final d = await api!.request('/api/personnel/direction/');
      if (mounted) {
        setState(() {
          data = d;
          error = '';
        });
      }
    } catch (e) {
      if (mounted) setState(() => error = '$e');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  List<Map<String, dynamic>> list(String key) =>
      List<Map<String, dynamic>>.from(data?[key] ?? []);
  String get name => data?['me']?['name'] ?? 'Personnel GO-MBOKA';
  Widget text(String s, {double size = 13, Color? color, FontWeight? weight}) =>
      Text(
        s,
        style: TextStyle(
          fontFamily: 'Inter',
          fontSize: size,
          color: color,
          fontWeight: weight,
        ),
      );
  Widget box(Widget child) => Container(
    padding: const EdgeInsets.all(18),
    decoration: BoxDecoration(
      color: surface,
      border: Border.all(color: border),
      borderRadius: BorderRadius.circular(14),
    ),
    child: child,
  );
  String fmt(dynamic v) {
    if (v == null) return '—';
    final n = v is num ? v : null;
    if (n != null) {
      final parts = n.toStringAsFixed(n % 1 == 0 ? 0 : 2).split('.');
      final whole = parts[0].replaceAllMapped(
        RegExp(r'(\d)(?=(\d{3})+(?!\d))'),
        (m) => '${m[1]} ',
      );
      return whole + (parts.length > 1 ? ',${parts[1]}' : '');
    }
    final date = DateTime.tryParse(v.toString());
    if (date != null) {
      final d = date.toLocal();
      return '${d.day.toString().padLeft(2, "0")}/${d.month.toString().padLeft(2, "0")}/${d.year} ${d.hour.toString().padLeft(2, "0")}:${d.minute.toString().padLeft(2, "0")}';
    }
    return v.toString();
  }

  Future<void> form(
    String title,
    List<String> fields,
    Future<void> Function(List<String>) save, {
    List<String>? initial,
    bool secret = false,
  }) async {
    final controllers = List.generate(
      fields.length,
      (i) => TextEditingController(text: initial?[i] ?? ''),
    );
    String localError = '';
    bool saving = false;
    await showDialog<void>(
      context: context,
      builder: (c) => StatefulBuilder(
        builder: (c, setDialog) => AlertDialog(
          title: Text(title),
          content: SizedBox(
            width: 420,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  for (int i = 0; i < fields.length; i++)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: TextField(
                        controller: controllers[i],
                        obscureText:
                            secret || fields[i].contains('Mot de passe'),
                        decoration: InputDecoration(labelText: fields[i]),
                      ),
                    ),
                  if (localError.isNotEmpty)
                    Text(
                      localError,
                      style: const TextStyle(color: Colors.redAccent),
                    ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: saving ? null : () => Navigator.pop(c),
              child: const Text('Annuler'),
            ),
            FilledButton(
              onPressed: saving
                  ? null
                  : () async {
                      setDialog(() => saving = true);
                      try {
                        await save(
                          controllers.map((x) => x.text.trim()).toList(),
                        );
                        if (c.mounted) Navigator.pop(c);
                      } catch (e) {
                        setDialog(() {
                          localError = '$e';
                          saving = false;
                        });
                      }
                    },
              child: Text(saving ? 'Enregistrement…' : 'Enregistrer'),
            ),
          ],
        ),
      ),
    );
    for (final controller in controllers) {
      controller.dispose();
    }
  }

  Future<void> connect() => form(
    'Connexion du personnel',
    ['Adresse du serveur', 'Téléphone', 'Mot de passe'],
    (v) async {
      final uri = Uri.tryParse(v[0]);
      if (uri == null ||
          !['http', 'https'].contains(uri.scheme) ||
          uri.host.isEmpty) {
        throw Exception('Adresse HTTP ou HTTPS requise.');
      }
      final candidate = PersonnelApi(v[0]);
      await candidate.login(v[1], v[2]);
      final snapshot = await candidate.request('/api/personnel/direction/');
      if (mounted) {
        setState(() {
          api = candidate;
          data = snapshot;
          error = '';
        });
      }
    },
    initial: [
      const String.fromEnvironment(
        'API_BASE_URL',
        defaultValue: 'http://127.0.0.1:8000',
      ),
      '',
      '',
    ],
  );
  Future<void> action(String action, Map<String, dynamic> values) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Confirmer cette modification ?'),
        content: const Text('La décision sera enregistrée sur le serveur.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(c, false),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(c, true),
            child: const Text('Confirmer'),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await api!.request(
        '/api/personnel/direction/',
        body: {'action': action, ...values},
      );
      await load();
    } catch (e) {
      if (mounted) setState(() => error = '$e');
    }
  }

  void select(int i) {
    setState(() {
      page = i;
      statusFilter = 'Tous';
    });
    if (scaffold.currentState?.isDrawerOpen ?? false) Navigator.pop(context);
  }

  Widget sidebar() => SizedBox(
    width: 252,
    child: Material(
      color: const Color(0xff171927),
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                const Icon(Icons.two_wheeler, color: accent, size: 32),
                const SizedBox(width: 12),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    text('GO-MBOKA', weight: FontWeight.bold, size: 15),
                    text('DIRECTION GÉNÉRALE', size: 10, color: muted),
                  ],
                ),
              ],
            ),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(12),
              children: [
                for (int i = 0; i < labels.length; i++)
                  ListTile(
                    selected: page == i,
                    selectedTileColor: const Color(0xff2b2741),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(9),
                    ),
                    dense: true,
                    leading: Icon(
                      icons[i],
                      size: 18,
                      color: page == i ? accent : muted,
                    ),
                    title: text(labels[i], color: page == i ? accent : muted),
                    onTap: () => select(i),
                  ),
              ],
            ),
          ),
          ListTile(
            leading: const CircleAvatar(
              backgroundColor: accent,
              child: Icon(Icons.person, color: Colors.white),
            ),
            title: text(name, size: 12),
            subtitle: text('Direction Générale', size: 10, color: muted),
            onTap: () => select(8),
          ),
        ],
      ),
    ),
  );
  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, c) {
      final desktop = c.maxWidth >= 1000;
      return Scaffold(
        key: scaffold,
        drawer: desktop ? null : Drawer(child: sidebar()),
        body: SafeArea(
          child: Row(
            children: [
              if (desktop) sidebar(),
              Expanded(
                child: Column(
                  children: [
                    Container(
                      height: 72,
                      padding: const EdgeInsets.symmetric(horizontal: 18),
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
                              crossAxisAlignment: CrossAxisAlignment.start,
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                text(
                                  labels[page],
                                  size: 16,
                                  weight: FontWeight.w600,
                                ),
                                text(
                                  data == null
                                      ? 'Connexion requise'
                                      : 'Synchronisé : ${fmt(data!['updated_at'])}',
                                  size: 10,
                                  color: muted,
                                ),
                              ],
                            ),
                          ),
                          IconButton(
                            tooltip: 'Actualiser',
                            onPressed: api == null || busy ? null : load,
                            icon: const Icon(Icons.refresh),
                          ),
                          IconButton(
                            tooltip: 'Notifications',
                            onPressed: () => select(6),
                            icon: Badge(
                              isLabelVisible: list(
                                'notifications',
                              ).any((n) => n['read'] == false),
                              child: const Icon(Icons.notifications_none),
                            ),
                          ),
                          IconButton(
                            tooltip: 'Compte',
                            onPressed: api == null ? connect : () => select(8),
                            icon: const Icon(
                              Icons.account_circle,
                              color: accent,
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (busy) const LinearProgressIndicator(minHeight: 2),
                    if (error.isNotEmpty)
                      MaterialBanner(
                        content: Text(error),
                        actions: [
                          TextButton(
                            onPressed: load,
                            child: const Text('Réessayer'),
                          ),
                        ],
                      ),
                    Expanded(
                      child: data == null
                          ? Center(
                              child: box(
                                Column(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    const Icon(
                                      Icons.lock_outline,
                                      size: 38,
                                      color: accent,
                                    ),
                                    const SizedBox(height: 16),
                                    text('Connectez-vous au serveur GO-MBOKA'),
                                    const SizedBox(height: 16),
                                    FilledButton(
                                      onPressed: connect,
                                      child: const Text('Connexion'),
                                    ),
                                  ],
                                ),
                              ),
                            )
                          : SingleChildScrollView(
                              padding: const EdgeInsets.all(24),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  if (page != 8)
                                    Padding(
                                      padding: const EdgeInsets.only(
                                        bottom: 16,
                                      ),
                                      child: TextField(
                                        onChanged: (s) =>
                                            setState(() => query = s),
                                        decoration: const InputDecoration(
                                          prefixIcon: Icon(Icons.search),
                                          hintText:
                                              'Rechercher dans cet onglet',
                                          border: OutlineInputBorder(),
                                          isDense: true,
                                        ),
                                      ),
                                    ),
                                  content(desktop),
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
  Widget content(bool desktop) {
    switch (page) {
      case 0:
        return overview(desktop);
      case 1:
        return gps();
      case 2:
        return motards();
      case 3:
        return table(
          'Clients',
          ['Nom', 'Téléphone', 'Courses', 'Dépenses FC', 'Inscription'],
          list('clients'),
          (r) => [r['name'], r['phone'], r['rides'], r['spent'], r['joined']],
        );
      case 4:
        return table(
          'Gérants de flotte',
          ['Nom', 'Téléphone', 'Motos', 'Assignées', 'Maintenance'],
          list('managers'),
          (r) => [
            r['name'],
            r['phone'],
            r['motorcycles'],
            r['assigned'],
            r['maintenance'],
          ],
        );
      case 5:
        return table(
          'Commissions enregistrées',
          [
            'Moto',
            'Propriétaire',
            'Début',
            'Fin',
            'Brut FC',
            'Commission FC',
            'Net FC',
          ],
          list('commissions'),
          (r) => [
            r['plate'],
            r['owner'],
            r['start'],
            r['end'],
            r['gross'],
            r['commission'],
            r['net'],
          ],
        );
      case 6:
        return notices();
      case 7:
        return support();
      default:
        return settings();
    }
  }

  List<Map<String, dynamic>> filtered(List<Map<String, dynamic>> rows) => rows
      .where(
        (r) => r.values.join(' ').toLowerCase().contains(query.toLowerCase()),
      )
      .toList();
  Widget table(
    String title,
    List<String> headers,
    List<Map<String, dynamic>> rows,
    List<dynamic> Function(Map<String, dynamic>) cells, {
    Widget Function(Map<String, dynamic>)? actions,
  }) => box(
    Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        text('$title · ${rows.length}', size: 15, weight: FontWeight.w600),
        const SizedBox(height: 12),
        if (filtered(rows).isEmpty)
          const Padding(
            padding: EdgeInsets.all(20),
            child: Text('Aucun résultat.'),
          )
        else
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(
              columnSpacing: 24,
              columns: [
                for (final h in headers) DataColumn(label: Text(h)),
                if (actions != null) const DataColumn(label: Text('Actions')),
              ],
              rows: [
                for (final r in filtered(rows))
                  DataRow(
                    cells: [
                      for (final value in cells(r)) DataCell(Text(fmt(value))),
                      if (actions != null) DataCell(actions(r)),
                    ],
                  ),
              ],
            ),
          ),
      ],
    ),
  );
  Widget overview(bool desktop) {
    final k = data!['kpis'];
    final metrics = [
      ('Courses aujourd’hui', fmt(k['total_rides'])),
      ('Motards actifs', '${k['active_motards']} / ${k['total_motards']}'),
      ('Revenus du jour', '${fmt(k['revenue_fc'])} FC'),
      (
        'Note moyenne',
        '${(k['avg_rating'] as num).toStringAsFixed(1).replaceAll(".", ",")} / 5',
      ),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        LayoutBuilder(
          builder: (c, b) => Wrap(
            spacing: 16,
            runSpacing: 16,
            children: [
              for (final (label, value) in metrics)
                SizedBox(
                  width: (b.maxWidth - (desktop ? 48 : 16)) / (desktop ? 4 : 2),
                  child: box(
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(Icons.insights, color: accent),
                        const SizedBox(height: 10),
                        text(value, size: 23, weight: FontWeight.bold),
                        text(label, size: 11, color: muted),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        if (desktop)
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(flex: 155, child: gps()),
              const SizedBox(width: 16),
              Expanded(
                flex: 100,
                child: Column(
                  children: [activity(), const SizedBox(height: 16), ranking()],
                ),
              ),
            ],
          )
        else ...[
          gps(),
          const SizedBox(height: 16),
          activity(),
          const SizedBox(height: 16),
          ranking(),
        ],
        const SizedBox(height: 18),
        motards(),
      ],
    );
  }

  Widget ranking() {
    final rows = list('motards')
      ..sort((a, b) => (b['rides'] as int).compareTo(a['rides'] as int));
    return box(
      Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          text('Top motards du jour', weight: FontWeight.w600),
          for (final r in rows.take(5))
            ListTile(
              dense: true,
              visualDensity: VisualDensity.compact,
              contentPadding: EdgeInsets.zero,
              title: text(r['name'], size: 12),
              subtitle: text(
                '${r['commune']} · ${r['rides']} courses',
                size: 10,
                color: muted,
              ),
              trailing: text('${fmt(r['revenue'])} FC', size: 12),
            ),
        ],
      ),
    );
  }

  Widget activity() {
    final hours = Map<String, dynamic>.from(data!['activity']);
    final max = hours.values.fold<double>(
      1,
      (m, v) => (v['count'] as num) > m ? (v['count'] as num).toDouble() : m,
    );
    return box(
      Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          text('Activité de la journée', weight: FontWeight.w600),
          text('Courses par heure · 00h → 23h', size: 10, color: muted),
          const SizedBox(height: 16),
          SizedBox(
            height: 120,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                for (int i = 0; i < 24; i++)
                  Expanded(
                    child: Tooltip(
                      message:
                          '${i}h · ${hours['$i']?['count'] ?? 0} courses · ${hours['$i']?['revenue'] ?? 0} FC',
                      child: Container(
                        margin: const EdgeInsets.symmetric(horizontal: 2),
                        height:
                            ((hours['$i']?['count'] ?? 0) as num).toDouble() /
                            max *
                            120,
                        decoration: BoxDecoration(
                          color: accent,
                          borderRadius: BorderRadius.circular(3),
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget motards() => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      Wrap(
        spacing: 8,
        children: [
          for (final s in ['Tous', 'pending', 'approved', 'rejected'])
            ChoiceChip(
              label: Text(
                {
                  'Tous': 'Tous',
                  'pending': 'À valider',
                  'approved': 'Validés',
                  'rejected': 'Rejetés',
                }[s]!,
              ),
              selected: statusFilter == s,
              onSelected: (_) => setState(() => statusFilter = s),
            ),
        ],
      ),
      const SizedBox(height: 12),
      table(
        'Motards du réseau',
        [
          'Nom',
          'Commune',
          'Dossier',
          'Abonnement',
          'Courses',
          'Revenu FC',
          'Note',
        ],
        list('motards')
            .where(
              (r) =>
                  statusFilter == 'Tous' ||
                  r['application_status'] == statusFilter,
            )
            .toList(),
        (r) => [
          r['name'],
          r['commune'],
          r['status'],
          r['subscription'],
          r['rides'],
          r['revenue'],
          r['rating'],
        ],
        actions: (r) => Wrap(
          children: [
            IconButton(
              tooltip: 'Voir le dossier',
              onPressed: () => showDialog<void>(
                context: context,
                builder: (c) => AlertDialog(
                  title: Text(r['name']),
                  content: Text(
                    'Téléphone : ${r['phone']}\nCommune : ${r['commune']}\nPermis : ${r['license']}\nIdentité : ${r['identity']}\nDocument : ${r['document'] ?? "Non fourni"}',
                  ),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(c),
                      child: const Text('Fermer'),
                    ),
                  ],
                ),
              ),
              icon: const Icon(Icons.visibility, size: 18),
            ),
            if (r['application_status'] == 'pending') ...[
              IconButton(
                tooltip: 'Approuver',
                onPressed: () => action('application', {
                  'id': r['profile_id'],
                  'status': 'approved',
                }),
                icon: const Icon(Icons.check, color: green, size: 18),
              ),
              IconButton(
                tooltip: 'Rejeter',
                onPressed: () => action('application', {
                  'id': r['profile_id'],
                  'status': 'rejected',
                }),
                icon: const Icon(
                  Icons.close,
                  color: Colors.redAccent,
                  size: 18,
                ),
              ),
            ],
          ],
        ),
      ),
    ],
  );
  Widget notices() => box(
    Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        text('Notifications', size: 16),
        if (filtered(list('notifications')).isEmpty)
          const Text('Aucune notification.'),
        for (final n in filtered(list('notifications')))
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: Icon(
              n['read'] ? Icons.notifications_none : Icons.notifications_active,
              color: accent,
            ),
            title: text(n['title']),
            subtitle: text(
              '${n['body']}\n${n['date']}',
              size: 11,
              color: muted,
            ),
            trailing: n['read']
                ? const Icon(Icons.done_all, color: green)
                : IconButton(
                    tooltip: 'Marquer comme lue',
                    onPressed: () =>
                        action('notification_read', {'id': n['id']}),
                    icon: const Icon(Icons.done),
                  ),
          ),
      ],
    ),
  );
  Widget support() => table(
    'Tickets support',
    ['Demandeur', 'Sujet', 'Priorité', 'Statut'],
    list('support'),
    (r) => [r['name'], r['subject'], r['priority'], r['status_label']],
    actions: (r) => PopupMenuButton<String>(
      tooltip: 'Traiter le ticket',
      onSelected: (s) => s == 'detail'
          ? showDialog<void>(
              context: context,
              builder: (c) => AlertDialog(
                title: Text(r['subject']),
                content: Text(r['message']),
                actions: [
                  TextButton(
                    onPressed: () => Navigator.pop(c),
                    child: const Text('Fermer'),
                  ),
                ],
              ),
            )
          : action('support_status', {'id': r['id'], 'status': s}),
      itemBuilder: (c) => [
        const PopupMenuItem(value: 'detail', child: Text('Voir le message')),
        for (final (v, l) in [
          ('open', 'Rouvrir'),
          ('in_progress', 'Prendre en charge'),
          ('resolved', 'Résoudre'),
        ])
          PopupMenuItem(value: v, child: Text(l)),
      ],
    ),
  );
  Widget gps() {
    final positions = filtered(list('positions'));
    return box(
      Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          text('Positions GPS — Kinshasa', weight: FontWeight.w600),
          const SizedBox(height: 12),
          if (positions.isEmpty)
            const SizedBox(
              height: 220,
              child: Center(child: Text('Aucune position GPS enregistrée.')),
            )
          else ...[
            SizedBox(
              height: 300,
              child: InteractiveViewer(
                minScale: 1,
                maxScale: 8,
                child: CustomPaint(
                  size: const Size(double.infinity, 300),
                  painter: PositionsPainter(positions),
                ),
              ),
            ),
            if (page == 1)
              for (final p in positions)
                ListTile(
                  dense: true,
                  leading: const Icon(
                    Icons.location_on,
                    color: green,
                    size: 17,
                  ),
                  title: text(p['name'], size: 12),
                  subtitle: text(
                    '${p['latitude']}, ${p['longitude']} · ${fmt(p['recorded_at'])}',
                    size: 10,
                    color: muted,
                  ),
                ),
          ],
        ],
      ),
    );
  }

  Widget settings() {
    final me = data!['me'];
    return box(
      Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          text('Mon compte', size: 18),
          const SizedBox(height: 16),
          text(name, size: 16),
          text('${me['phone']} · ${me['email']}'),
          const SizedBox(height: 16),
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              FilledButton(
                onPressed: () => form(
                  'Modifier le profil',
                  ['Prénom', 'Nom', 'E-mail'],
                  (v) async {
                    await api!.request(
                      '/api/v1/auth/me/',
                      method: 'PATCH',
                      body: {
                        'first_name': v[0],
                        'last_name': v[1],
                        'email': v[2],
                      },
                    );
                    await load();
                  },
                  initial: [
                    me['first_name'] ?? '',
                    me['last_name'] ?? '',
                    me['email'] ?? '',
                  ],
                ),
                child: const Text('Modifier le profil'),
              ),
              OutlinedButton(
                onPressed: () => form(
                  'Changer le mot de passe',
                  ['Mot de passe actuel', 'Nouveau mot de passe', 'Confirmer'],
                  (v) async {
                    await api!.request(
                      '/api/account/password/',
                      body: {
                        'old_password': v[0],
                        'new_password': v[1],
                        'new_password2': v[2],
                      },
                    );
                  },
                  secret: true,
                ),
                child: const Text('Changer le mot de passe'),
              ),
              OutlinedButton(
                onPressed: load,
                child: const Text('Actualiser les données'),
              ),
              TextButton(
                onPressed: () {
                  api?.token = null;
                  setState(() {
                    api = null;
                    data = null;
                    error = '';
                    page = 0;
                  });
                },
                child: const Text('Déconnexion'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class PositionsPainter extends CustomPainter {
  final List<Map<String, dynamic>> positions;
  PositionsPainter(this.positions);
  @override
  void paint(Canvas canvas, Size s) {
    canvas.drawRect(Offset.zero & s, Paint()..color = const Color(0xff191d2e));
    const west = 15.20, east = 15.65, north = -4.20, south = -4.55;
    for (final p in positions) {
      final x = ((p['longitude'] as num) - west) / (east - west) * s.width;
      final y = (north - (p['latitude'] as num)) / (north - south) * s.height;
      if (x < 0 || x > s.width || y < 0 || y > s.height) continue;
      canvas.drawCircle(Offset(x, y), 7, Paint()..color = green);
      final label = TextPainter(
        text: TextSpan(
          text: p['name'],
          style: const TextStyle(
            fontFamily: 'Inter',
            color: Colors.white,
            fontSize: 10,
          ),
        ),
        textDirection: TextDirection.ltr,
      )..layout(maxWidth: 120);
      label.paint(canvas, Offset(x.clamp(0, s.width - 120), y + 10));
    }
    final t = TextPainter(
      text: const TextSpan(
        text:
            'KINSHASA · Positions enregistrées\n15.20°E → 15.65°E / 4.20°S → 4.55°S',
        style: TextStyle(fontFamily: 'Inter', fontSize: 10, color: muted),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    t.paint(canvas, const Offset(8, 8));
  }

  @override
  bool shouldRepaint(covariant PositionsPainter old) => true;
}
