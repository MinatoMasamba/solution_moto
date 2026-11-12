import 'dart:convert';
import 'dart:typed_data';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';
import '../../core/api.dart';
import '../../theme/personnel_theme.dart';

class PersonnelProfilePage extends StatefulWidget {
  const PersonnelProfilePage({
    super.key,
    required this.api,
    required this.onSaved,
    required this.changePassword,
    required this.logout,
  });
  final PersonnelApi api;
  final ValueChanged<Map<String, dynamic>> onSaved;
  final VoidCallback changePassword, logout;
  @override
  State<PersonnelProfilePage> createState() => _ProfileState();
}

class _ProfileState extends State<PersonnelProfilePage> {
  final form = GlobalKey<FormState>();
  final fields = {
    for (final name in [
      'first_name',
      'last_name',
      'post_nom',
      'email',
      'phone_number',
    ])
      name: TextEditingController(),
  };
  Map<String, dynamic>? profile;
  bool saving = false;
  String? error, success;
  String mode = 'light';
  Uint8List? photo;
  @override
  void initState() {
    super.initState();
    load();
  }

  @override
  void dispose() {
    for (final c in fields.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> load() async {
    try {
      final p = await widget.api.request('/api/personnel/profile/');
      if (!mounted) return;
      setState(() {
        profile = p;
        mode = p['theme'] ?? 'light';
        for (final entry in fields.entries) {
          entry.value.text = p[entry.key] ?? '';
        }
        error = null;
      });
    } catch (e) {
      if (mounted) setState(() => error = '$e');
    }
  }

  Future<void> choosePhoto() async {
    try {
      final file = await openFile(
        acceptedTypeGroups: [
          const XTypeGroup(
            label: 'Image de profil',
            extensions: ['jpg', 'jpeg', 'png'],
            mimeTypes: ['image/jpeg', 'image/png'],
          ),
        ],
      );
      if (file == null) return;
      if (await file.length() > 1024 * 1024) {
        throw Exception('Choisir une photo de moins de 1 Mo.');
      }
      final bytes = await file.readAsBytes();
      if (mounted) setState(() => photo = bytes);
    } catch (e) {
      if (mounted) setState(() => error = '$e');
    }
  }

  Future<void> save() async {
    if (!(form.currentState?.validate() ?? false)) return;
    setState(() {
      saving = true;
      error = null;
      success = null;
    });
    try {
      final result = await widget.api.request(
        '/api/personnel/profile/',
        method: 'PATCH',
        body: {
          for (final e in fields.entries) e.key: e.value.text.trim(),
          'theme': mode,
          if (photo != null) 'photo_base64': base64Encode(photo!),
        },
      );
      if (!mounted) return;
      setState(() {
        profile = result;
        photo = null;
        success = 'Profil enregistré.';
      });
      widget.onSaved(result);
      PersonnelTheme.apply(result['theme']);
    } catch (e) {
      if (mounted) setState(() => error = '$e');
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  String date(dynamic value) {
    if (value == null) return 'Non disponible';
    final d = DateTime.tryParse('$value')?.toLocal();
    return d == null
        ? 'Non disponible'
        : '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year}';
  }

  Widget card(String title, Widget child) => Card(
    margin: const EdgeInsets.only(bottom: 18),
    elevation: 0,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(14),
      side: BorderSide(color: Theme.of(context).dividerColor),
    ),
    child: Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            title,
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 20),
          child,
        ],
      ),
    ),
  );
  Widget field(String name, String label, {TextInputType? keyboard}) =>
      TextFormField(
        controller: fields[name],
        enabled: !saving,
        keyboardType: keyboard,
        decoration: InputDecoration(labelText: label),
        validator: (value) {
          final v = value?.trim() ?? '';
          if (name == 'phone_number' &&
              !RegExp(r'^\+?[0-9 ]{8,20}$').hasMatch(v)) {
            return 'Téléphone valide requis';
          }
          if (name == 'email' &&
              v.isNotEmpty &&
              !RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(v)) {
            return 'Adresse e-mail invalide';
          }
          return null;
        },
      );
  @override
  Widget build(BuildContext context) {
    final p = profile;
    if (p == null) {
      return Center(
        child: error != null
            ? Column(
                children: [
                  Text(error!),
                  TextButton(onPressed: load, child: const Text('Réessayer')),
                ],
              )
            : const CircularProgressIndicator(),
      );
    }
    final ImageProvider? image = photo != null
        ? MemoryImage(photo!)
        : p['photo_url'] != null
        ? NetworkImage(p['photo_url'] as String)
        : null;
    return Form(
      key: form,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (error != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text(
                error!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ),
          if (success != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text(
                success!,
                style: const TextStyle(color: Colors.green),
              ),
            ),
          card(
            'Mon profil',
            Wrap(
              spacing: 22,
              runSpacing: 18,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                CircleAvatar(
                  radius: 42,
                  backgroundColor: Theme.of(
                    context,
                  ).colorScheme.primary.withValues(alpha: .12),
                  backgroundImage: image,
                  child: image == null
                      ? Icon(
                          Icons.person_outline,
                          size: 42,
                          color: Theme.of(context).colorScheme.primary,
                        )
                      : null,
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      p['name'],
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(p['role']),
                    const SizedBox(height: 6),
                    Text(
                      p['is_active'] == true
                          ? 'Compte actif'
                          : 'Compte inactif',
                      style: TextStyle(
                        color: p['is_active'] == true
                            ? Colors.green
                            : Colors.orange,
                      ),
                    ),
                  ],
                ),
                OutlinedButton.icon(
                  onPressed: saving ? null : choosePhoto,
                  icon: const Icon(Icons.add_a_photo_outlined, size: 18),
                  label: const Text('Changer la photo'),
                ),
              ],
            ),
          ),
          card(
            'Informations personnelles',
            LayoutBuilder(
              builder: (context, c) {
                final w = c.maxWidth >= 640
                    ? (c.maxWidth - 18) / 2
                    : c.maxWidth;
                return Wrap(
                  spacing: 18,
                  runSpacing: 20,
                  children: [
                    for (final (name, label) in [
                      ('first_name', 'Prénom'),
                      ('last_name', 'Nom'),
                      ('post_nom', 'Post-nom'),
                      ('email', 'E-mail'),
                      ('phone_number', 'Téléphone de connexion'),
                    ])
                      SizedBox(
                        width: w,
                        child: field(
                          name,
                          label,
                          keyboard: name == 'email'
                              ? TextInputType.emailAddress
                              : name == 'phone_number'
                              ? TextInputType.phone
                              : TextInputType.name,
                        ),
                      ),
                  ],
                );
              },
            ),
          ),
          card(
            'Préférences d’affichage',
            DropdownButtonFormField<String>(
              initialValue: mode,
              decoration: const InputDecoration(
                labelText: 'Thème de l’application',
              ),
              items: const [
                DropdownMenuItem(value: 'light', child: Text('Clair')),
                DropdownMenuItem(value: 'dark', child: Text('Sombre')),
                DropdownMenuItem(
                  value: 'system',
                  child: Text('Suivre le système'),
                ),
              ],
              onChanged: saving
                  ? null
                  : (value) => setState(() => mode = value!),
            ),
          ),
          card(
            'Sécurité et accès',
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Rôle attribué : ${p['role']}'),
                const SizedBox(height: 10),
                Text('Compte créé le ${date(p['date_joined'])}'),
                const SizedBox(height: 10),
                Text('Dernière connexion : ${date(p['last_login'])}'),
                const SizedBox(height: 10),
                Text(
                  p['is_verified'] == true
                      ? 'Identité vérifiée'
                      : 'Identité non vérifiée',
                ),
                const SizedBox(height: 18),
                Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: [
                    OutlinedButton.icon(
                      onPressed: saving ? null : widget.changePassword,
                      icon: const Icon(Icons.lock_outline, size: 18),
                      label: const Text('Changer le mot de passe'),
                    ),
                    TextButton.icon(
                      onPressed: saving ? null : widget.logout,
                      icon: const Icon(Icons.logout, size: 18),
                      label: const Text('Déconnexion'),
                    ),
                  ],
                ),
              ],
            ),
          ),
          Wrap(
            alignment: WrapAlignment.end,
            spacing: 12,
            runSpacing: 12,
            children: [
              OutlinedButton(
                onPressed: saving
                    ? null
                    : () {
                        setState(() {
                          photo = null;
                          success = null;
                        });
                        load();
                      },
                child: const Text('Annuler les modifications'),
              ),
              FilledButton.icon(
                onPressed: saving ? null : save,
                icon: saving
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.save_outlined, size: 18),
                label: Text(
                  saving ? 'Enregistrement…' : 'Enregistrer le profil',
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
