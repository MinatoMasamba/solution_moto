import 'dart:convert';
import 'dart:io';

/// Shared authenticated transport for all personnel roles. Tokens stay in memory.
class PersonnelApi {
  final Uri base;
  String? token;
  PersonnelApi(String url) : base = Uri.parse(url);
  Future<Map<String, dynamic>> request(
    String path, {
    Map<String, dynamic>? body,
    String? method,
  }) async {
    final client = HttpClient()
      ..connectionTimeout = const Duration(seconds: 15);
    try {
      final req = await client.openUrl(
        method ?? (body == null ? 'GET' : 'POST'),
        base.resolve(path),
      );
      req.headers.contentType = ContentType.json;
      if (token != null) req.headers.set('Authorization', 'Bearer $token');
      if (body != null) {
        final bytes = utf8.encode(jsonEncode(body));
        req.contentLength = bytes.length;
        req.add(bytes);
      }
      final res = await req.close().timeout(const Duration(seconds: 20));
      final text = await utf8.decoder.bind(res).join();
      if (res.statusCode >= 400) {
        throw HttpException('Erreur ${res.statusCode} : $text');
      }
      return jsonDecode(text) as Map<String, dynamic>;
    } finally {
      client.close(force: true);
    }
  }

  Future<Map<String, dynamic>> login(String username, String password) async {
    final result = await request(
      '/api/v1/auth/login/',
      body: {'phone_number': username, 'password': password},
    );
    token = result['access'] as String;
    try {
      return await request('/api/v1/auth/me/');
    } catch (_) {
      token = null;
      rethrow;
    }
  }
}
