<%! import onlinejudge_template.generator.cplusplus as cplusplus %>\
<%
    data['config']['indent'] = '\t'
    data['config']['scanner'] = 'cin'
    data['config']['printer'] = 'cout'
    data['config']['using_namespace_std'] = False
%>\
#include <iostream>
#include <vector>

${cplusplus.return_type(data)} solve(${cplusplus.arguments_types(data)}) {
	// TODO: edit here
}

int main() {
${cplusplus.read_input(data)}
	auto ans = solve(${cplusplus.arguments(data)});
${cplusplus.write_output(data)}
	return 0;
}
