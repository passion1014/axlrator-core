import unittest

from app.process.java_parser import extract_methods_from_java

# 위의 함수들이 이미 선언되었다고 가정합니다.
class TestExtractMethodsFromJava(unittest.TestCase):

    def test_extract_single_method(self):
        java_code = """
        public class Example {
            public void myMethod(int a, String b) {
                System.out.println(a + b);
            }
        }
        """
        methods = extract_methods_from_java(java_code)
        
        # 단일 메서드 검증
        self.assertEqual(len(methods), 1)
        self.assertEqual(methods[0]['name'], 'myMethod')
        self.assertEqual(methods[0]['return_type'], 'void')
        self.assertEqual(methods[0]['parameters'], 'int a, String b')
        self.assertIn('System.out.println(a + b);', methods[0]['code'])

    def test_extract_multiple_methods(self):
        java_code = """
        public class Example {
            public void firstMethod() {
                System.out.println("First Method");
            }
            
            private int secondMethod(int x) {
                return x * 2;
            }
        }
        """
        methods = extract_methods_from_java(java_code)

        # 다중 메서드 검증
        self.assertEqual(len(methods), 2)

        # 첫 번째 메서드 검증
        self.assertEqual(methods[0]['name'], 'firstMethod')
        self.assertEqual(methods[0]['return_type'], 'void')
        self.assertEqual(methods[0]['parameters'], '')
        self.assertIn('System.out.println("First Method");', methods[0]['code'])

        # 두 번째 메서드 검증
        self.assertEqual(methods[1]['name'], 'secondMethod')
        self.assertEqual(methods[1]['return_type'], 'int')
        self.assertEqual(methods[1]['parameters'], 'int x')
        self.assertIn('return x * 2;', methods[1]['code'])
        
        for method in methods:
            print(method)

    def test_no_methods(self):
        java_code = """
        public class Example {
            // This class has no methods
        }
        """
        methods = extract_methods_from_java(java_code)
        
        # 메서드가 없어야 함
        self.assertEqual(len(methods), 0)

if __name__ == '__main__':
    unittest.main(buffer=True)
    
# 실행 명령어
# python -m unittest discover -s test -p "test_java_parser.py"