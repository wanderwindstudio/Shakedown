Shader "Planet/Sky"
{
    Properties { _Horizon("Lavender horizon",Color)=(.57,.51,.64,1) _Zenith("Blue zenith",Color)=(.09,.20,.34,1) _SunColor("Amber sun",Color)=(1,.65,.28,1) _SunDirection("Sun direction",Vector)=(.4,.3,-.5,0) }
    SubShader
    {
        Tags { "Queue"="Background" "RenderType"="Background" "PreviewType"="Skybox" "RenderPipeline"="UniversalPipeline" }
        Cull Off ZWrite Off
        Pass
        {
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            struct A { float3 p:POSITION; }; struct V { float4 p:SV_POSITION; float3 dir:TEXCOORD0; };
            CBUFFER_START(UnityPerMaterial)
            float4 _Horizon,_Zenith,_SunColor,_SunDirection;
            CBUFFER_END
            V Vert(A i) { V o; o.p=TransformObjectToHClip(i.p); o.dir=i.p; return o; }
            half4 Frag(V i):SV_Target
            {
                float3 d=normalize(i.dir); float sun=saturate(dot(d,normalize(_SunDirection.xyz)));
                float3 c=lerp(_Horizon.rgb,_Zenith.rgb,pow(saturate(d.y),.55));
                c=lerp(c,_SunColor.rgb,pow(sun,7)*.48);
                c+=_SunColor.rgb*(pow(sun,380)*.5+smoothstep(.9995,.9997,sun)*3);
                return half4(c,1);
            }
            ENDHLSL
        }
    }
}
