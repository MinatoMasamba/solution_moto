import 'dart:convert';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_mboka/core/api.dart';

void main() {
  test(
    'JWT login follows Django phone_number contract and sends bearer',
    () async {
      final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      addTearDown(() => server.close(force: true));
      final calls = <String>[];
      server.listen((req) async {
        calls.add(req.uri.path);
        req.response.headers.contentType = ContentType.json;
        if (req.uri.path == '/api/v1/auth/login/') {
          final body = jsonDecode(await utf8.decoder.bind(req).join());
          expect(body, {
            'phone_number': '+243000000000',
            'password': 'test-only',
          });
          req.response.write(jsonEncode({'access': 'test-token'}));
        } else {
          expect(req.headers.value('Authorization'), 'Bearer test-token');
          req.response.write(
            jsonEncode({'role': 'OPERATOR', 'first_name': 'Test'}),
          );
        }
        await req.response.close();
      });
      final api = PersonnelApi('http://127.0.0.1:${server.port}');
      final me = await api.login('+243000000000', 'test-only');
      expect(me['role'], 'OPERATOR');
      expect(calls, ['/api/v1/auth/login/', '/api/v1/auth/me/']);
    },
  );
}
